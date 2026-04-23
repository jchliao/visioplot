import matplotlib.pyplot as plt


def cm(*args):
    return tuple(x / 2.54 for x in args)


DEFAULT_STYLE = {
    # ===== 1. Figure =====
    "figure.figsize": cm(9, 6.75),
    "svg.fonttype": "none",
    # ===== 2. Font =====
    "font.family": ["Times New Roman", "SimSun"],
    "mathtext.fontset": "stix",
    "axes.unicode_minus": False,
    "font.size": 9,  # 小五
    "figure.titlesize": 10.5,  # 五号
    "axes.titlesize": 10.5,  # 五号
    "axes.labelsize": 9,  # 小五
    "xtick.labelsize": 7.5,  # 六号
    "ytick.labelsize": 7.5,  # 六号
    "legend.fontsize": 7.5,  # 六号
    # ===== 3. Lines & Axes =====
    "lines.linewidth": 0.75,
    "axes.linewidth": 0.5,
    "grid.linewidth": 0.5,
    # ===== 4. Ticks =====
    "xtick.direction": "in",
    "xtick.major.size": 3,
    "xtick.major.width": 0.5,
    "xtick.minor.size": 1.5,
    "xtick.minor.width": 0.5,
    "xtick.top": True,
    "ytick.direction": "in",
    "ytick.major.size": 3,
    "ytick.major.width": 0.5,
    "ytick.minor.size": 1.5,
    "ytick.minor.width": 0.5,
    "ytick.right": True,
    # ===== 5. Legend =====
    "legend.frameon": False,
    # ===== 6. Layout =====
    # todo: 改变了布局方式，需要修改 out 逻辑才行
    # "figure.constrained_layout.use": True,
    # "figure.constrained_layout.w_pad": 0.04,
    # "figure.constrained_layout.h_pad": 0.01,
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
