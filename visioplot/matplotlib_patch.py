import functools
import logging
from matplotlib.font_manager import FontProperties, get_font, fontManager
from matplotlib._mathtext import get_unicode_index


def _patch_fallback(self, uniindex: int):
    """补丁逻辑：在用户指定的字体族列表中寻找缺失字符"""
    families = self.default_font_prop.get_family()
    search_list = families[1:]
    for fam in search_list:
        try:
            prop = FontProperties(family=fam)
            path = fontManager.findfont(prop, fallback_to_default=False)
            ft = get_font(path)
            if ft.get_char_index(uniindex) != 0:
                return ft, uniindex, False
        except Exception:
            continue
    return None


def mathtext_fallback_decorator(func):
    @functools.wraps(func)
    def wrapper(self, fontname, font_class, sym):
        level = logging.getLogger("matplotlib.mathtext").getEffectiveLevel()
        logging.getLogger("matplotlib.mathtext").setLevel(logging.ERROR)
        font, uniindex, slanted = func(self, fontname, font_class, sym)
        logging.getLogger("matplotlib.mathtext").setLevel(level)
        if uniindex == 0xA4:
            real_uni = get_unicode_index(sym)
            res = _patch_fallback(self, real_uni)
            if res:
                return res
        return font, uniindex, slanted

    return wrapper
