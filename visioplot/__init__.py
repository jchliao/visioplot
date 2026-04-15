from .matplotlib_utils import apply_style, cm, reset_style
from .debug_utils import set_debug
from .parse_utils import parse_latex_like
from .svg_utils import Fig, modify_axis, modify_line_path, savefig
from .visiolib import VisioExporter

__version__ = "1.0.0"

__all__ = [
	"VisioExporter",
	"Fig",
	"savefig",
	"modify_line_path",
	"modify_axis",
	"parse_latex_like",
	"set_debug",
	"apply_style",
	"reset_style",
	"cm",
]
