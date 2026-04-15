from .matplotlib_utils import apply_style, cm, reset_style
from .debug_utils import set_debug
from .svg_utils import Fig, savefig
from .visiolib import VisioExporter

__version__ = "1.0.12"


__all__ = [
    "VisioExporter",
    "Fig",
    "savefig",
    "set_debug",
    "apply_style",
    "reset_style",
    "cm",
]
