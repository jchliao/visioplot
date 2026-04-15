# %%
import matplotlib.pyplot as plt
import mpl_toolkits.axisartist as AA

import visioplot.matplotlib_utils as mpu
import visioplot.svg_utils as su


mpu.apply_style()


def example1_axisartist_svg_only():
    """示例1：使用 axisartist 生成可编辑 SVG。"""
    plt.figure(figsize=mpu.cm(9, 6.75))
    plt.axes(axes_class=AA.Axes)
    plt.plot([1, 2, 3], [3, 5, 4], label="inax", marker="s")
    plt.plot(
        [1, 2, 3], [5, 15, 3], gid="out", label="outax", linestyle="--", marker="o"
    )
    plt.xlim([1.25, 3])
    plt.ylim([4.0, 10.0])
    plt.legend()
    su.savefig("example1_axisartist.svg")
    print("example1 done: example1_axisartist.svg")



def example2_fig_object_svg_only():
    """示例2：通过 Fig(fig).savefig 导出 SVG。"""
    fig = plt.figure(figsize=mpu.cm(9, 6.75))
    ax = fig.add_subplot(axes_class=AA.Axes)
    ax.plot([1, 2, 3], [3, 2, 4], label="inax")
    ax.plot([1, 2, 3], [5, 15, 3], label="outax", gid="out")
    ax.set_ylim((0, 10))
    ax.legend()
    su.Fig(fig).savefig("example2_fig.svg")
    print("example2 done: example2_fig.svg")



def example3_text_markup_to_visio_clipboard():
    """示例3：测试文本样式解析并复制到剪贴板。"""
    plt.figure(figsize=mpu.cm(9, 6.75))
    plt.plot([0, 1, 2], [0, 4, 2], "k-")
    plt.xlabel("x^*2*/m  *斜体x*  **粗体x**  ***粗斜x***")
    plt.ylabel("y_a^b  y_{*i*}^{**2**}  ***Y***_{test}")
    plt.title("A_a测试Test  *斜体*  **粗体**  ***粗斜体***")
    plt.text(1, 3, "P_*wind* = **A**^2 + **B**")
    plt.tight_layout()
    exporter = su.savefig("example3_text.svg", bbox_inches="tight", pad_inches=0.1)
    exporter.toclip()
    print("example3 done: example3_text.svg + clipboard")



def example4_parser_stress_to_visio_clipboard():
    """示例4：批量文本分支覆盖并复制到剪贴板。"""
    plt.figure(figsize=mpu.cm(8, 8))
    test_items = [
        "1. 基础样式: **加粗**, *斜体*, ***粗斜体***",
        "2. 基础上下标: H_2O, x^2, e^{i\\pi} + 1 = 0",
        "3. 样式嵌套: **粗体中包含*斜体***",
        "4. 下标带样式: 变量_**max**, 索引_{i,*j*}",
        "5. 复杂组合: ***A***_{sub}^{sup} + **B**_{1}^{2}",
        "6. 深度包裹: x^{y^{z}}, A_{n_{i+1}}",
        "7. 混合样式: *abc **def** ghi*",
        "8. A_***ab**c***, A_{*ab*}",
    ]
    for i, text in enumerate(test_items):
        plt.text(0.1, 0.85 - i * 0.12, text)
    plt.axis("off")
    plt.tight_layout()
    exporter = su.savefig("example4_parser.svg", bbox_inches="tight", pad_inches=0.1)
    exporter.toclip()
    print("example4 done: example4_parser.svg + clipboard")


EXAMPLES = {
    "1": example1_axisartist_svg_only,
    "2": example2_fig_object_svg_only,
    "3": example3_text_markup_to_visio_clipboard,
    "4": example4_parser_stress_to_visio_clipboard,
}


def main():
    for key in ["1", "2", "3", "4"]:
        EXAMPLES[key]()


if __name__ == "__main__":
    main()

# %%
