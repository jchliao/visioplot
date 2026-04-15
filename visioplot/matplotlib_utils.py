import matplotlib.pyplot as plt
import matplotlib_inline

DEFAULT_STYLE = {
    "font.family": ["Times New Roman", "SimSun"],
    "mathtext.fontset": "stix",
    "axes.unicode_minus": False,
    "svg.fonttype": "none",
    "font.size": 7.5,
    "lines.linewidth": 0.75,
}


def apply_style(style=None, *, inline_svg=True):
    """Apply the default plotting style or a custom style mapping."""
    if inline_svg:
        matplotlib_inline.backend_inline.set_matplotlib_formats("svg")
    plt.rcParams.update(DEFAULT_STYLE if style is None else style)


def reset_style():
    """Restore matplotlib defaults."""
    plt.rcdefaults()

def cm(*args):
    return tuple(x / 2.54 for x in args)
