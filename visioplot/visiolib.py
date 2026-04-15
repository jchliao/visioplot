from pathlib import Path
import re
import sys

from visioplot.parse_utils import parse_latex_like, visPosNormal

if sys.platform == "win32":
    import win32com.client


visCharacterStyle = 2
visCharacterPosition = 4

visPosSuper = 1
visPosSub = 2

visBold = 1
visItalic = 2

PATTERN = re.compile(r"[\*\_\^]")


def apply_script_formatting(shape):
    text = shape.Text
    if not text:
        return
    segments = parse_latex_like(text)
    plain_text = "".join(seg[0] for seg in segments)
    shape.Text = plain_text
    pos = 0
    chars = shape.Characters
    for seg_text, seg_pos, italic_flag, bold_flag in segments:
        if seg_pos == visPosNormal and not italic_flag and not bold_flag:
            pos += len(seg_text)
            continue
        length = len(seg_text)
        chars.Begin = pos
        chars.End = pos + length
        chars.CharProps(visCharacterPosition, seg_pos)
        style = 0
        if italic_flag:
            style |= visItalic
        if bold_flag:
            style |= visBold
        chars.CharProps(visCharacterStyle, style)
        pos += length


def set_locpinx_no_move(shape, target_formula):
    """
    修改 LocPinX 的同时补偿 PinX，确保形状在页面上的物理位置保持不动。
    原理：新 PinX = 旧 PinX + (新 LocPinX 数值 - 旧 LocPinX 数值)
    """
    old_pinx = shape.Cells("PinX").ResultIU
    old_locpinx = shape.Cells("LocPinX").ResultIU
    shape.Cells("LocPinX").FormulaU = target_formula
    new_locpinx = shape.Cells("LocPinX").ResultIU
    shape.Cells("PinX").ResultIU = old_pinx + (new_locpinx - old_locpinx)


def adjust_text_width(shape):
    align_value = shape.CellsU("Para.HorzAlign").ResultIU
    if align_value == 0:
        set_locpinx_no_move(shape, "0")
    elif align_value == 2:
        set_locpinx_no_move(shape, "Width*1")
    shape.Cells("Width").FormulaU = "GUARD(TEXTWIDTH(TheText) + 1pt)"


def iter_shapes(shape):
    yield shape
    if hasattr(shape, "Shapes"):
        try:
            for sub in shape.Shapes:
                yield from iter_shapes(sub)
        except Exception:
            return


class VisioExporter:
    visio = None

    def __init__(self, svg_path):
        self.svg_path = Path(svg_path).resolve()

    def toclip(self, vsdx_path=None, clipboard=True):
        return self.tovsd(vsdx_path=vsdx_path, clipboard=clipboard)

    def tovsd(self, vsdx_path=None, clipboard=False):
        try:
            VisioExporter.visio = win32com.client.GetActiveObject("Visio.Application")
        except Exception:
            VisioExporter.visio = win32com.client.Dispatch("Visio.Application")
        document = None
        try:
            document = VisioExporter.visio.Documents.Open(str(self.svg_path))
            page = VisioExporter.visio.ActivePage
            VisioExporter.visio.ScreenUpdating = False
            page.PageSheet.CellsU("DrawingScale").FormulaU = "1 mm"
            page.PageSheet.CellsU("PageScale").FormulaU = "1 mm"
            for shape in page.Shapes:
                for sub_shape in iter_shapes(shape):
                    if hasattr(sub_shape, "Text") and sub_shape.Text:
                        if PATTERN.search(sub_shape.Text):
                            apply_script_formatting(sub_shape)
                        adjust_text_width(sub_shape)
            if clipboard:
                win = VisioExporter.visio.ActiveWindow
                win.SelectAll()
                try:
                    win.Selection.Ungroup()
                except Exception:
                    pass
                win.Selection.Copy()
            VisioExporter.visio.ScreenUpdating = True
            vsdx_path = Path(vsdx_path or self.svg_path).with_suffix(".vsdx")
            document.SaveAs(str(vsdx_path))
        except Exception as e:
            print(f"发生错误: {e}")
        finally:
            if document:
                document.Close()
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