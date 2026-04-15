from pathlib import Path
import re
import sys

from visioplot.debug_utils import debug_print, error_print, warn_print
from visioplot.parse_utils import parse_latex_like, visPosNormal

if sys.platform == "win32":
    import win32com.client


visCharacterStyle = 2
visCharacterPosition = 4

visPosSuper = 1
visPosSub = 2

visBold = 1
visItalic = 2

visCharacterFont = 0
visCharacterAsianFont = 51

PATTERN = re.compile(r"[\*\_\^]")
GREEK_PATTERN = re.compile(r'[α-ωΑ-Ω]')  # 匹配希腊字母（包括大写和小写）


def _get_font_id(shape, font_name: str):
    """Return Visio font ID if available, else None."""
    try:
        return shape.Document.Fonts(font_name).ID
    except Exception:
        return None


def apply_script_formatting(shape):
    text = shape.Text
    if not text:
        return
    font_id = _get_font_id(shape, "Times New Roman")
    segments = parse_latex_like(text)
    plain_text = "".join(seg[0] for seg in segments)
    shape.Text = plain_text
    pos = 0
    chars = shape.Characters
    for seg_text, seg_pos, italic_flag, bold_flag in segments:
        # --- 遍历每个字符检查是否为希腊字母 ---
        for i in range(len(seg_text)):
            char = seg_text[i]
            # 如果字符是希腊字母，设置字体
            if GREEK_PATTERN.match(char):
                chars.Begin = pos + i
                chars.End = pos + i + 1
                # chars.CharProps(visCharacterFont, font_id)
                # 强制设置visCharacterAsianFont为新罗马,修复visio的bug导致部分希腊字母无法正确显示的问题
                chars.CharProps(visCharacterAsianFont, font_id)
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
    
    def _is_visio_running(self):
        """
        私有方法：检查当前保存的 Visio 实例是否仍然有效运行
        返回 True = 有效可用；False = 已关闭/失效
        """
        visio = VisioExporter.visio
        if visio is None:
            return False

        try:
            # 尝试访问 Visio 版本属性，能访问说明进程存活
            _version = visio.Version
            return True
        except Exception:
            # 访问失败 = 进程已被关闭/失效
            VisioExporter.visio = None
            return False

    def toclip(self, vsdx_path=None, clipboard=True):
        return self.tovsd(vsdx_path=vsdx_path, clipboard=clipboard)

    def tovsd(self, vsdx_path=None, clipboard=False):
        if sys.platform != "win32":
            warn_print("Visio export is only supported on Windows with Visio installed.")
            return self
        debug_print(
            f"VisioExporter.tovsd start: svg='{self.svg_path}', clipboard={clipboard}"
        )
        if not self._is_visio_running():
            try:
                VisioExporter.visio = win32com.client.GetActiveObject("Visio.Application")
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
            page.PageSheet.CellsU("DrawingScale").FormulaU = "1 mm"
            page.PageSheet.CellsU("PageScale").FormulaU = "1 mm"
            for shape in page.Shapes:
                for sub_shape in iter_shapes(shape):
                    if hasattr(sub_shape, "Text") and sub_shape.Text:
                        if PATTERN.search(sub_shape.Text):
                            apply_script_formatting(sub_shape)
                        adjust_text_width(sub_shape)
            if clipboard:
                win = visio.ActiveWindow
                win.SelectAll()
                try:
                    win.Selection.Ungroup()
                except Exception:
                    pass
                win.Selection.Copy()
            visio.ScreenUpdating = True
            vsdx_path = Path(vsdx_path or self.svg_path).with_suffix(".vsdx")
            document.SaveAs(str(vsdx_path))
            debug_print(f"VSDX saved: '{vsdx_path}'")
        except Exception as e:
            error_print(f"发生错误: {e}")
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