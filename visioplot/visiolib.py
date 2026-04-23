from pathlib import Path
import sys
import array
from visioplot.debug_utils import debug_print, error_print, warn_print
from visioplot.parse_utils import parse_latex_like
from visioplot.visioapp import VisioApp
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
    visXFormHeight,
    visSectionObject,
    visRowXFormOut,
    visSelTypeAll,
    visTypeGroup,
    visSelTypeByType,
    visSelModeOnlySuper,
    visRowText,
    visTxtBlkVerticalAlign,
    visVertMiddle,
    visTypeSelGroup,
    visComplexItalic,
    visComplexBold,
    visSpaceLine,
)


# GREEK_PATTERN = re.compile(r"[α-ωΑ-Ω]")  # 匹配希腊字母（包括大写和小写）
# GREEK_SET = set("αβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ")
def is_greek(ch):
    return (
        0x0370 <= ord(ch) <= 0x03FF  # Greek & Coptic
    )


def apply_script_formatting(shape, text):
    chars = shape.Characters
    if not any(c in text for c in "*_^"):
        _apply_greek_formatting(chars, text, 0, force_italic=True)
        return
    segments = parse_latex_like(text)
    shape.Text = "".join(seg[0] for seg in segments)
    pos = 0
    for seg_text, seg_pos, italic_flag, bold_flag in segments:
        has_greek = _apply_greek_formatting(chars, seg_text, pos)
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
            if has_greek:
                style |= visComplexItalic
        if bold_flag:
            style |= visBold
            if has_greek:
                style |= visComplexBold
        chars.CharProps(visCharacterStyle, style)
        pos += length


def _apply_greek_formatting(chars, text_segment, offset, force_italic=False):
    has_greek = False
    for i, char in enumerate(text_segment):
        if not is_greek(char):
            continue
        has_greek = True
        char_idx = offset + i
        chars.Begin = char_idx
        chars.End = char_idx + 1
        chars.CharProps(visCharacterAsianFont, 0)
        if force_italic:
            chars.CharProps(visCharacterStyle, visItalic | visComplexItalic)
    return has_greek


READ_CONFIG = [
    [visSectionObject, visRowXFormOut, visXFormPinX],  # 获取 PinX
    [visSectionObject, visRowXFormOut, visXFormWidth],  # 获取 Width
    # [visSectionObject, visRowXFormOut, visXFormHeight],  # 获取 Height
    [visSectionParagraph, visRowParagraph, visHorzAlign],  # 获取对齐方式
]
READ_STREAM = array.array("h", sum(READ_CONFIG, []))
WRITE_CONFIG = [
    [visSectionObject, visRowXFormOut, visXFormPinX],  # PinX
    [visSectionObject, visRowXFormOut, visXFormLocPinX],  # LocPinX
    [visSectionObject, visRowXFormOut, visXFormWidth],  # Width
    [visSectionObject, visRowXFormOut, visXFormHeight],  # Height
    [visSectionObject, visRowText, visTxtBlkVerticalAlign],  # 垂直对齐方式
    [visSectionParagraph, visRowParagraph, visSpaceLine],  # 行间距
]
WRITE_STREAM = array.array("h", sum(WRITE_CONFIG, []))
ALIGN_MAP = {
    "0": 0.0,
    "1": 0.5,
    "2": 1.0,
}  # visHorzLeft=0, visHorzCenter=1, visHorzRight=2


def eval_in(expr: str) -> str:
    if " in" in expr:
        result = eval(expr.replace(" in", ""))
        return f"{result}"
    return expr


def fit_shape_to_text(shape):
    formulas = shape.GetFormulasU(READ_STREAM)
    old_pinx_f, old_width_f, align_f = formulas
    target = ALIGN_MAP.get(align_f, 0.5)
    new_pinx_formula = eval_in(f"{old_pinx_f} + {old_width_f}*{target - 0.5}")
    new_locpinx_formula = f"Width*{target}"
    new_width_f = "TEXTWIDTH(TheText)"
    new_height_f = "TEXTHEIGHT(TheText, Width)"
    new_formulas = [
        new_pinx_formula,
        new_locpinx_formula,
        new_width_f,
        new_height_f,
        visVertMiddle,
        "-100%",
    ]
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


def ungroup(page):
    try:
        page.CreateSelection(
            visSelTypeByType, visSelModeOnlySuper, visTypeSelGroup
        ).Ungroup()
    except Exception:
        pass


def updatebox(page):
    try:
        page.CreateSelection(
            visSelTypeByType, visSelModeOnlySuper, visTypeSelGroup
        ).UpdateAlignmentBox()
    except Exception:
        pass


class VisioExporter:
    def __init__(self, svg_path):
        self.svg_path = Path(svg_path).resolve()

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
            warn_print("Only supported on Windows.")
            return self

        visio = VisioApp.get()
        visio.ScreenUpdating = False
        visio.EventsEnabled = False
        visio.DeferRecalc = True
        visio.UndoEnabled = False
        try:
            document = visio.Documents.Open(str(self.svg_path))
            page = visio.ActivePage
            ungroup(page)

            for sub_shape in iter_shapes(page):
                txt = sub_shape.Text
                if not txt:
                    continue
                apply_script_formatting(sub_shape, txt)
                fit_shape_to_text(sub_shape)
            modify_all_fill_patterns(document)
            sheet = page.PageSheet
            sheet.CellsU("DrawingScale").FormulaU = "1 mm"
            sheet.CellsU("PageScale").FormulaU = "1 mm"
            updatebox(page)
            visio.DeferRecalc = False
            visio.EventsEnabled = True
            visio.ScreenUpdating = True
            self.safe_save(document, vsdx_path)
            if clipboard:
                page.CreateSelection(visSelTypeAll).Copy()
            document.Close()
        except Exception as e:
            error_print(f"发生错误: {e}")
        finally:
            visio.DeferRecalc = False
            visio.EventsEnabled = True
            visio.ScreenUpdating = True
            visio.UndoEnabled = True
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
