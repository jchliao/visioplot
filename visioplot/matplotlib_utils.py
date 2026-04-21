import matplotlib.pyplot as plt


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
        try:
            from matplotlib_inline.backend_inline import set_matplotlib_formats

            set_matplotlib_formats("svg")
        except Exception:
            pass
    if style is None:
        plt.rcParams.update(DEFAULT_STYLE)
    else:
        final_style = DEFAULT_STYLE.copy()
        final_style.update(style)
        plt.rcParams.update(final_style)


def reset_style():
    """Restore matplotlib defaults."""
    plt.rcdefaults()


def cm(*args):
    return tuple(x / 2.54 for x in args)
