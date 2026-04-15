# %%
import matplotlib.pyplot as plt
import mpl_toolkits.axisartist as AA
import visioplot as vp

# %%
vp.apply_style()


def example1_axisartist_svg_only():
    """示例1：使用 axisartist 生成可编辑 SVG。"""
    plt.figure(figsize=vp.cm(9, 6.75))
    plt.axes(axes_class=AA.Axes)
    plt.plot([1, 2, 3], [3, 5, 4], label="inax", marker="s")
    plt.plot(
        [1, 2, 3], [5, 15, 3], gid="out", label="outax", linestyle="--", marker="o"
    )
    plt.xlim([1.25, 3])
    plt.ylim([4.0, 10.0])
    plt.legend()
    vp.savefig("example1_axisartist.svg")
    print("example1 done: example1_axisartist.svg")



def example2_fig_object_svg_only():
    """示例2：通过 Fig(fig).savefig 导出 SVG。"""
    fig = plt.figure(figsize=vp.cm(9, 6.75))
    ax = fig.add_subplot(axes_class=AA.Axes)
    ax.plot([1, 2, 3], [3, 2, 4], label="inax")
    ax.plot([1, 2, 3], [5, 15, 3], label="outax", gid="out")
    ax.set_ylim((0, 10))
    ax.legend()
    vp.Fig(fig).savefig("example2_fig.svg")
    print("example2 done: example2_fig.svg")



def example3_text_markup_to_visio_clipboard():
    """示例3：公式标注场景（导出到 Visio 保留字符样式）。"""
    plt.figure(figsize=vp.cm(9, 6.75))
    q = [0, 20, 40, 60, 80]
    dp = [3.2, 4.1, 5.7, 7.8, 10.4]
    plt.plot(q, dp, marker="o")

    plt.xlabel("流量 q_**in** / (m^3/h)")
    plt.ylabel("压降 Δp / kPa")
    plt.title("泵特性曲线: H = H_0 - k q^2")
    plt.text(20, 8.8, "η_{*pump*} = **0.86**")
    plt.text(20, 7.9, "功率关系: P = ρ g q H")
    plt.tight_layout()

    exporter = vp.savefig(
        "example3_formula_text.svg", bbox_inches="tight", pad_inches=0.1
    )
    exporter.toclip()
    print("example3 done: example3_formula_text.svg + clipboard")


def example4_parser_stress_to_visio_clipboard():
    """示例4：项目周报模板（批量文本块 + Visio 粘贴）。"""
    plt.figure(figsize=vp.cm(8, 8))
    test_lines = [
        "1) 【基础样式】**项目A**: 进度 ***92%***, 重点风险: *供货周期*",
        "2) 【上下标】效率指标: η_{line1}=**0.88**, η_{line2}=**0.84**",
        "3) 【上下标嵌套】能耗: E_{m_{1~3月}}= 12.8, 12.1, 11.4 kWh/t",
        "4) 【复杂组合】设备状态: T_1^{max}=78℃, P_2^avg=0.62MPa",
        "5) 【粗斜体】结论: ***建议本月执行阀门检修***",
        "6) 【混合场景】备注:  x_i, y_{i+1} e^{iπ} = -1",
    ]

    x_pos = 0.1
    start_y = 0.9
    line_gap = 0.14
    for i, text in enumerate(test_lines):
        plt.text(x_pos, start_y - i * line_gap, text)

    plt.axis("off")
    plt.tight_layout()
    exporter = vp.savefig("example4_parser.svg", bbox_inches="tight", pad_inches=0.1)
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
