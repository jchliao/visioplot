import functools
import logging
import matplotlib as mpl
from matplotlib.font_manager import FontProperties, get_font, fontManager
from matplotlib._mathtext import get_unicode_index


def _patch_fallback(uniindex: int):
    """补丁逻辑：在系统字体中寻找缺失字符"""
    families = mpl.rcParams.get("font.family", [])
    if isinstance(families, str):
        families = [families]

    search_list = families + mpl.rcParams.get("font.sans-serif", [])

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
        if uniindex == 0xA4:
            real_uni = get_unicode_index(sym)
            logging.getLogger("matplotlib.mathtext").setLevel(level)
            res = _patch_fallback(real_uni)
            if res:
                return res
        return font, uniindex, slanted

    return wrapper
