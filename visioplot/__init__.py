from .matplotlib_utils import apply_style, cm, reset_style
from .debug_utils import set_debug
from .svg_exporter import Fig, savefig
from .visio_exporter import VisioExporter
from matplotlib._mathtext import UnicodeFonts
from .matplotlib_patch import mathtext_fallback_decorator

__version__ = "1.2.2"


__all__ = [
    "VisioExporter",
    "Fig",
    "savefig",
    "set_debug",
    "apply_style",
    "reset_style",
    "cm",
]

# --- 执行注入 ---
UnicodeFonts._get_glyph = mathtext_fallback_decorator(UnicodeFonts._get_glyph)
