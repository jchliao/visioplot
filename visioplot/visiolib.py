from pathlib import Path
import re
import sys
import os
import array
from visioplot.debug_utils import debug_print, error_print, warn_print
from visioplot.parse_utils import parse_latex_like

if sys.platform == "win32":
    import win32com.client as win32c
    import win32job
    import win32process
    import win32api
    import win32con

from visioplot.visconst import (
    visCharacterStyle,
    visCharacterPos,
    visBold,
    visItalic,
    visCharacterAsianFont,
    visSectionParagraph,
    visHorzAlign,
    visPosNormal,
    visRowParagraph,
    visXFormPinX,
    visXFormPinY,
    visXFormLocPinX,
    visXFormWidth,
    visSectionObject,
    visRowXFormOut,
    visSelTypeAll,
    visTypeGroup,
    visSelTypeByType,
    visSelModeSkipSuper,
    visTypeSelGroup,
    visWSMinimized,
)


GREEK_PATTERN = re.compile(r"[α-ωΑ-Ω]")  # 匹配希腊字母（包括大写和小写）


def apply_script_formatting(shape, text):
    segments = parse_latex_like(text)
    plain_text = "".join(seg[0] for seg in segments)
    shape.Text = plain_text
    pos = 0
    chars = shape.Characters
    for seg_text, seg_pos, italic_flag, bold_flag in segments:
        if GREEK_PATTERN.search(seg_text):
            for i, char in enumerate(seg_text):
                if GREEK_PATTERN.match(char):
                    chars.Begin = pos + i
                    chars.End = pos + i + 1
                    chars.CharProps(visCharacterAsianFont, 0)
        if seg_pos == visPosNormal and not italic_flag and not bold_flag:
            pos += len(seg_text)
            continue
        length = len(seg_text)
        chars.Begin = pos
        chars.End = pos + length
        chars.CharProps(visCharacterPos, seg_pos)
        style = 0
        if italic_flag:
            style |= visItalic
        if bold_flag:
            style |= visBold
        chars.CharProps(visCharacterStyle, style)
        pos += length


READ_CONFIG = [
    [visSectionObject, visRowXFormOut, visXFormPinX],  # 获取 PinX
    [visSectionObject, visRowXFormOut, visXFormWidth],  # 获取 Width
    [visSectionParagraph, visRowParagraph, visHorzAlign],  # 获取对齐方式
]
READ_STREAM = array.array("h", sum(READ_CONFIG, []))
WRITE_CONFIG = [
    [visSectionObject, visRowXFormOut, visXFormPinX],  # PinX
    [visSectionObject, visRowXFormOut, visXFormLocPinX],  # LocPinX
    [visSectionObject, visRowXFormOut, visXFormWidth],  # Width
]
WRITE_STREAM = array.array("h", sum(WRITE_CONFIG, []))
ALIGN_MAP = {"0": 0.0, "1": 0.5, "2": 1.0}


def adjust_text_width(shape):
    formulas = shape.GetFormulasU(READ_STREAM)
    old_pinx_f, old_width_f, align_f = formulas
    target = ALIGN_MAP.get(align_f, 0.5)
    new_pinx_formula = f"{old_pinx_f} + {old_width_f}*{target - 0.5}"
    new_locpinx_formula = f"Width*{target}"
    new_width_f = "GUARD(TEXTWIDTH(TheText))"
    new_formulas = [new_pinx_formula, new_locpinx_formula, new_width_f]
    shape.SetFormulas(WRITE_STREAM, new_formulas, 0)


def iter_shapes(parent):
    try:
        shapes = parent.Shapes
    except Exception as e:
        error_print(f"Error occurred while iterating shapes: {e}")
        return
    for s in shapes:
        yield s
        if s.Type == visTypeGroup:
            try:
                yield from iter_shapes(s)
            except Exception as e:
                warn_print(f"Skip bad group: {e}")
                continue


class VisioExporter:
    visio = None
    _job = None

    def __init__(self, svg_path):
        self.svg_path = Path(svg_path).resolve()

    @classmethod
    def _bind_lifecycle(cls, visio):
        if cls._job is None:
            # 创建 Job 对象
            cls._job = win32job.CreateJobObject(None, f"VisioJob_{os.getpid()}")
            if cls._job is None:
                error_print("Failed to create Job object for Visio process management.")
                return
            info = win32job.QueryInformationJobObject(
                cls._job, win32job.JobObjectExtendedLimitInformation
            )
            # 核心：Job 句柄关闭时，自动强制结束内部所有进程
            info["BasicLimitInformation"]["LimitFlags"] |= (
                win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            )
            win32job.SetInformationJobObject(
                cls._job, win32job.JobObjectExtendedLimitInformation, info
            )
        hwnd = visio.Application.WindowHandle32
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        access = win32con.PROCESS_TERMINATE | win32con.PROCESS_SET_QUOTA
        handle = win32api.OpenProcess(access, False, pid)

        try:
            win32job.AssignProcessToJobObject(cls._job, handle)
        finally:
            win32api.CloseHandle(handle)

    @classmethod
    def get_visio(cls):
        if cls.visio is not None:
            try:
                _ = cls.visio.Version
                return cls.visio
            except Exception:
                cls.visio = None
        cls.visio = win32c.DispatchEx("Visio.Application")
        cls.visio.Visible = False
        cls._bind_lifecycle(cls.visio)
        return cls.visio

    @classmethod
    def exit(cls):
        if cls.visio:
            try:
                cls.visio.AlertResponse = 6  # IDYES 保存剪切板数据
                cls.visio.Quit()
            except Exception:
                pass
            finally:
                cls.visio = None
        if cls._job:
            win32api.CloseHandle(cls._job)
            cls._job = None

    def safe_save(self, document, vsdx_path):
        target = Path(vsdx_path or self.svg_path)
        vsdx_path = target.with_suffix(".vsdx").resolve()
        directory = vsdx_path.parent
        stem = vsdx_path.stem
        suffix = vsdx_path.suffix
        final_path = vsdx_path
        counter = 1
        while final_path.exists():
            try:
                with open(final_path, "r+"):
                    break
            except (PermissionError, OSError):
                final_path = directory / f"{stem}({counter}){suffix}"
                counter += 1
        document.SaveAs(str(final_path))
        debug_print(f"VSDX saved: '{final_path}'")

    def toclip(self, vsdx_path=None, clipboard=True):
        return self.tovsd(vsdx_path=vsdx_path, clipboard=clipboard)

    def tovsd(self, vsdx_path=None, clipboard=False):
        if sys.platform != "win32":
            warn_print(
                "Visio export is only supported on Windows with Visio installed."
            )
            return self
        debug_print(
            f"VisioExporter.tovsd start: svg='{self.svg_path}', clipboard={clipboard}"
        )
        # if not (visio := self.get_visio()):
        #     return self
        visio = VisioExporter.get_visio()
        try:
            document = visio.Documents.Open(str(self.svg_path))
            debug_print("SVG document opened in Visio")
            page = visio.ActivePage
            visio.ScreenUpdating = False
            visio.EventsEnabled = False
            visio.DeferRecalc = True
            visio.UndoEnabled = False
            page.PageSheet.CellsU("DrawingScale").FormulaU = "1 mm"
            page.PageSheet.CellsU("PageScale").FormulaU = "1 mm"
            try:
                page.CreateSelection(
                    visSelTypeByType, visSelModeSkipSuper, visTypeSelGroup
                ).Ungroup()
            except Exception:
                pass
            for sub_shape in iter_shapes(page):
                txt = sub_shape.Text
                if not txt:
                    continue
                if any(c in txt for c in "*_^"):
                    apply_script_formatting(sub_shape, txt)
                adjust_text_width(sub_shape)
            modify_all_fill_patterns(document)
            visio.DeferRecalc = False
            visio.EventsEnabled = True
            visio.ScreenUpdating = True
            visio.UndoEnabled = True
            self.safe_save(document, vsdx_path)
            if clipboard:
                page.CreateSelection(visSelTypeAll).Copy()
            document.Close()
        except Exception as e:
            VisioExporter.exit()
            error_print(f"发生错误: {e}")
        return self


PATTERN_WRITE_CONFIG = [
    [visSectionObject, visRowXFormOut, visXFormPinX],
    [visSectionObject, visRowXFormOut, visXFormPinY],
]
PATTERN_WRITE_STREAM = array.array("h", sum(PATTERN_WRITE_CONFIG, []))


def modify_all_fill_patterns(doc):
    for master in doc.Masters:
        master_edit = master.Open()
        for shp in master_edit.Shapes:
            sid = shp.NameID
            for subshp in shp.Shapes:
                subshp.SetFormulas(
                    PATTERN_WRITE_STREAM,
                    [f"{sid}!Width*0.5", f"{sid}!Height*0.5"],
                    0,
                )
        master_edit.Close()
