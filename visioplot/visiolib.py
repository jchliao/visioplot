from pathlib import Path
import re
import sys
import array
from visioplot.debug_utils import debug_print, error_print, warn_print
from visioplot.parse_utils import parse_latex_like

if sys.platform == "win32":
    import win32com.client

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
    visSelModeSkipSub,
    visTypeSelGroup,
)


PATTERN = re.compile(r"[\*\_\^]")
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
        shps = parent.Shapes
        for i in range(1, shps.Count + 1):
            s = shps.Item(i)
            yield s
            if s.Type == visTypeGroup:
                yield from iter_shapes(s)
    except Exception:
        return


class VisioExporter:
    visio = None

    def __init__(self, svg_path):
        self.svg_path = Path(svg_path).resolve()

    def _is_visio_running(self):
        visio = VisioExporter.visio
        if visio is None:
            return False
        try:
            # 尝试访问 Visio 版本属性，能访问说明进程存活
            _version = visio.Version
            return True
        except Exception:
            VisioExporter.visio = None
            return False

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
        if not self._is_visio_running():
            try:
                VisioExporter.visio = win32com.client.GetActiveObject(
                    "Visio.Application"
                )
                debug_print("Connected to existing Visio instance")
            except Exception:
                VisioExporter.visio = win32com.client.Dispatch("Visio.Application")
                debug_print("Started new Visio instance")

        visio = VisioExporter.visio
        if visio is None:
            error_print("无法创建或连接 Visio 实例")
            return self

        document = None
        try:
            document = visio.Documents.Open(str(self.svg_path))
            debug_print("SVG document opened in Visio")
            page = visio.ActivePage
            visio.ScreenUpdating = False
            visio.EventsEnabled = False
            visio.DeferRecalc = True
            page.PageSheet.CellsU("DrawingScale").FormulaU = "1 mm"
            page.PageSheet.CellsU("PageScale").FormulaU = "1 mm"
            try:
                page.CreateSelection(
                    visSelTypeByType, visSelModeSkipSub, visTypeSelGroup
                ).Ungroup()
            except Exception:
                pass
            for sub_shape in iter_shapes(page):
                txt = sub_shape.Text
                if txt:
                    if PATTERN.search(txt):
                        apply_script_formatting(sub_shape, txt)
                    adjust_text_width(sub_shape)
            modify_all_fill_patterns(document)
            visio.DeferRecalc = False
            if clipboard:
                page.CreateSelection(visSelTypeAll).Copy()
            visio.EventsEnabled = True
            visio.ScreenUpdating = True

            vsdx_path = Path(vsdx_path or self.svg_path).with_suffix(".vsdx")
            document.SaveAs(str(vsdx_path))
            debug_print(f"VSDX saved: '{vsdx_path}'")
        except Exception as e:
            error_print(f"发生错误: {e}")
        finally:
            if document:
                document.Close()
            if not clipboard:
                self.exit()
        return self

    @classmethod
    def exit(cls):
        if cls.visio:
            try:
                cls.visio.Quit()
            except Exception:
                pass
            finally:
                cls.visio = None


PATTERN_WRITE_CONFIG = [
    [visSectionObject, visRowXFormOut, visXFormPinX],
    [visSectionObject, visRowXFormOut, visXFormPinY],
]
PATTERN_WRITE_STREAM = array.array("h", sum(PATTERN_WRITE_CONFIG, []))


def modify_all_fill_patterns(doc):
    for master in doc.Masters:
        master_edit = master.Open()
        for shp in master_edit.Shapes:
            for subshp in shp.Shapes:
                subshp.SetFormulas(
                    PATTERN_WRITE_STREAM, ["Sheet.5!Width*0.5", "Sheet.5!Height*0.5"], 0
                )
        master_edit.Close()
