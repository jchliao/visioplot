# Visioplot

Visioplot 是一个面向科研绘图与工程汇报场景的 Python 工具库，重点提供：

- Matplotlib 图形导出为结构更易编辑的 SVG。
- SVG 转 Visio（VSDX）和剪贴板导出。
- 类 LaTeX 文本样式解析（上下标、粗体、斜体、粗斜体）。

## 适用场景

- 在 Python 中完成绘图后，需要在 Visio/PPT 继续精修图形。
- 需要把超出坐标轴范围的曲线做可编辑线段化处理。
- 需要在 Visio 中保留部分文本样式（例如上下标、粗斜体）。

## 安装

如果你在当前仓库开发：

```bash
pip install -e .
```

如果后续发布到包仓库：

```bash
pip install visioplot
```

## 环境要求

- Python >= 3.12
- 主要依赖：matplotlib、beautifulsoup4、lxml
- Visio 导出功能需要：Windows + Microsoft Visio + pywin32

## 快速开始

### 1) 统一绘图样式

```python
import visioplot as vp

vp.apply_style()
```

### 2) 普通 plt 流程导出 SVG

```python
import matplotlib.pyplot as plt
import visioplot as vp

vp.apply_style()

plt.plot([1, 2, 3], [3, 5, 4], label="inax", marker="s")
plt.plot([1, 2, 3], [5, 15, 3], gid="out", label="outax", linestyle="--", marker="o")
plt.legend()

vp.savefig("demo.svg")
```

### 3) Figure 对象导出 SVG

```python
import matplotlib.pyplot as plt
import mpl_toolkits.axisartist as AA
import visioplot as vp

vp.apply_style()

fig = plt.figure()
ax = fig.add_subplot(axes_class=AA.Axes)
ax.plot([1, 2, 3], [3, 2, 4], label="inax")
ax.plot([1, 2, 3], [5, 15, 3], gid="out", label="outax")
ax.legend()

vp.Fig(fig).savefig("demo_fig.svg")
```

### 4) 导出到 Visio（VSDX / 剪贴板）

```python
import matplotlib.pyplot as plt
import visioplot as vp

vp.apply_style()

plt.plot([1, 2, 3], [3, 5, 4], label="inax", marker="s")
plt.plot([1, 2, 3], [5, 15, 3], gid="out", label="outax", linestyle="--", marker="o")
plt.legend()

exporter = vp.savefig("demo.svg")
exporter.tovsd()   # 保存为 demo.vsdx
exporter.toclip()  # 导出并复制到剪贴板
```

## 调试输出

库默认关闭 debug 输出。需要查看解析/导出调试信息时：

```python
import visioplot as vp

vp.set_debug(True)
# ... run your code
vp.set_debug(False)
```

## main.py 示例

仓库根目录的 main.py 提供 4 个完整示例，覆盖：

1. axisartist + SVG 导出
2. Fig(fig) + SVG 导出
3. 公式文本样式 + Visio 剪贴板导出
4. 复杂文本组合 + Visio 剪贴板导出

直接运行：

```bash
python main.py
```

当前示例输出文件：

- example1_axisartist.svg
- example2_fig.svg
- example3_formula_text.svg
- example4_parser.svg

## API 概览

### 包级导出（visioplot）

- apply_style(style=None, inline_svg=True)
- reset_style()
- cm(*args)
- set_debug(enabled=True)
- savefig(path, **kwargs) -> VisioExporter
- Fig(fig).savefig(path, **kwargs) -> VisioExporter
- modify_line_path(path_element)
- modify_axis(svg_content)
- parse_latex_like(text)
- VisioExporter(svg_path)

### VisioExporter

- tovsd(vsdx_path=None, clipboard=False)
- toclip(vsdx_path=None, clipboard=True)
- exit()

## 文本语法（简版）

- 斜体：*text*
- 粗体：**text**
- 粗斜体：***text***
- 下标：x_2、x_{abc}
- 上标：x^2、x^{abc}
- 下标斜体：c_*x*

## 常见问题

### Q1: tovsd() 或 toclip() 报错

请检查：

- 是否在 Windows 上运行
- 是否安装了 Microsoft Visio
- 是否安装了 pywin32

### Q2: 我只想要 SVG，不需要 Visio

只调用 vp.savefig("xxx.svg") 即可，不要调用 tovsd()/toclip()。

### Q3: 为什么有些字符字体在 Visio 里会变化

Visio 对不同字符会做字体回退。当前代码已对部分希腊字符做专门处理，但具体效果仍取决于本机字体与 Visio 字体映射。

## License

MIT
