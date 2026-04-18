import copy
import io
from pathlib import Path
import re
from bs4 import BeautifulSoup, Tag
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.pyplot import gcf
from visioplot.visiolib import VisioExporter


class Fig:
    def __init__(self, fig):
        self.fig: Figure = copy.deepcopy(fig)

    def savefig(self, *args, **kwargs) -> VisioExporter:
        kwargs["format"] = "svg"
        fig = self.fig
        ax = fig.get_axes()[0]

        # 第一次渲染并解析 (主图)
        svg_buffer = io.BytesIO()
        fig.savefig(svg_buffer, **kwargs)
        svg_buffer.seek(0)
        main_soup = BeautifulSoup(svg_buffer.read(), "xml")

        # 传入对象，直接进行原位修改，返回标志位
        flag_out = _svg_windows(main_soup)

        if flag_out:
            bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
            ax.set_axis_off()
            legend = ax.get_legend()
            if legend:
                legend.remove()
            kwargs["bbox_inches"] = bbox
            svg_buffer = io.BytesIO()
            fig.savefig(svg_buffer, **kwargs)
            svg_buffer.seek(0)
            sub_soup = BeautifulSoup(svg_buffer.read(), "xml")
            _svg_content(sub_soup)
            # 将数据层节点合并到主图中 (直接在对象间操作)
            _combined_svg(main_soup, sub_soup)

        # 修改坐标轴统一清理
        modify_axis(main_soup)
        modify_path_extend_clip(main_soup)
        _svg_clean(main_soup)

        plt.close(fig)
        fname = Path(args[0]).with_suffix(".svg")
        with open(fname, "w", encoding="utf-8") as file:
            file.write(main_soup.prettify())

        return VisioExporter(fname)


def savefig(*args, **kwargs) -> VisioExporter:
    fig = gcf()
    return Fig(fig).savefig(*args, **kwargs)


# 所有的辅助函数现在直接接收 BeautifulSoup 对象，并在原位(in-place)修改
def _svg_clean(soup: BeautifulSoup):
    for useless_tag in soup.find_all(["metadata", "style", "clipPath"]):
        useless_tag.decompose()
    for tag_with_clip in soup.find_all(attrs={"clip-path": True}):
        del tag_with_clip["clip-path"]
    for g_tag in reversed(soup.find_all("g")):
        g_id = g_tag.get("id") or ""
        if g_id == "ax" or g_id == "line-id" or g_id in AXIS_ID_LIST:
            continue
        has_relevant_id = any(k in g_id for k in ["legend", "figure", "axes"])
        has_single_child = len(g_tag.find_all(recursive=False)) <= 1
        if has_relevant_id or has_single_child:
            g_tag.unwrap()
    for tag in reversed(soup.find_all(["g", "defs"])):
        if not tag.find() and not tag.get_text(strip=True):
            tag.decompose()


def _svg_windows(soup: BeautifulSoup):
    flag_out = False
    for g_tag in soup.find_all("g", id="out"):
        defs_tag = Tag(name="defs")
        for path_tag in g_tag.find_all("path"):
            if path_tag.get("id") is not None:
                path_tag_tmp = path_tag.copy_self()
                defs_tag.append(path_tag_tmp)
                break
        g_tag.replace_with(defs_tag)
        flag_out = True
    return flag_out


def _svg_content(soup: BeautifulSoup):
    svg_root = soup.find("svg")
    if svg_root is None:
        return
    viewbox_attr = svg_root.get("viewBox") or "0 0 0 0"
    viewbox = str(viewbox_attr).split()
    width = float(viewbox[2])
    height = float(viewbox[3])
    out_elements = soup.find_all("g", id="out")
    out_point_defs_id = []
    svg_root.clear()

    if len(out_elements) == 0:
        return

    for out_element in out_elements:
        for path_tag in out_element.find_all("path"):
            if path_tag.get("clip-path") is not None:
                modify_line_path(path_tag)
            out_point_defs_id.append(path_tag.get("id", ""))

        all_g = out_element.find_all("g")
        for g_tag in all_g:
            if g_tag.get("clip-path") is not None:
                for use_tag in g_tag.find_all("use"):
                    x = float(str(use_tag.get("x") or 0))
                    y = float(str(use_tag.get("y") or 0))
                    if x < 0 or x > width or y < 0 or y > height:
                        use_tag.decompose()

    ax_group = soup.new_tag("g", id="ax")
    for out_element in out_elements:
        ax_group.append(out_element.extract())
    svg_root.append(ax_group)


def _combined_svg(main_soup: BeautifulSoup, sub_soup: BeautifulSoup):
    cp_tag = main_soup.find("clipPath")
    rect_tag = cp_tag.find("rect") if cp_tag else None
    ax_tag = sub_soup.find("g", id="ax")
    axes_tag = main_soup.find("g", id="axes_1")
    if rect_tag and ax_tag and axes_tag:
        rect_x = rect_tag.get("x") or "0"
        rect_y = rect_tag.get("y") or "0"
        ax_tag["transform"] = f"translate({rect_x}, {rect_y})"
        axes_tag.insert(2, ax_tag.extract())


def modify_line_path(path: Tag):
    target_path = path if path.name == "path" else path.find("path")
    if not target_path:
        return
    d_attr = str(target_path.get("d", ""))
    # 使用正则匹配指令(M/L/z等)和数字(包括负数和小数)
    tokens = re.findall(r"[MLZmlz]|[+-]?\d*\.?\d+", d_attr)

    lines_to_create = []
    current_pos = None
    i = 0

    while i < len(tokens):
        token = tokens[i]

        if token.upper() == "M":
            # M 指令：移动当前点
            current_pos = (tokens[i + 1], tokens[i + 2])
            i += 3
        elif token.upper() == "L":
            # L 指令：从当前点连线到目标点
            new_pos = (tokens[i + 1], tokens[i + 2])
            if current_pos:
                lines_to_create.append((current_pos, new_pos))
            current_pos = new_pos
            i += 3
        else:
            # 兼容处理：如果没有显式指令但有连续坐标（SVG 允许 M x y x2 y2 隐式转 L）
            i += 1

    if not lines_to_create:
        return

    # 样式处理
    style = str(target_path.get("style", ""))
    if "stroke-linecap" in style:
        style = style.replace("stroke-linecap:square", "stroke-linecap:round").replace(
            "stroke-linecap: square", "stroke-linecap: round"
        )
    else:
        style = (style.rstrip(";") + "; stroke-linecap: round").lstrip("; ")

    # 创建容器
    g = Tag(name="g", attrs={"id": "line-id", "style": style})
    if cp := target_path.get("clip-path"):
        g["clip-path"] = cp

    # 填充 line 标签
    for p1, p2 in lines_to_create:
        line = Tag(name="line")
        line["x1"], line["y1"] = p1
        line["x2"], line["y2"] = p2
        # 注意：原 path 的 stroke 属性通常在 style 或单独属性中，line 会继承 g 的样式
        g.append(line)

    target_path.replace_with(g)


AXIS_ID_LIST = [
    "mpl_toolkits.axisartist.axis_artist_1",
    "mpl_toolkits.axisartist.axis_artist_2",
    "mpl_toolkits.axisartist.axis_artist_3",
    "mpl_toolkits.axisartist.axis_artist_4",
]


def modify_axis(soup: BeautifulSoup):
    if not (svg_root := soup.find("svg")):
        return
    axis_groups = svg_root.find_all("g", id=AXIS_ID_LIST)
    for g_tag in axis_groups:
        paths = g_tag.find_all("path", id=False)
        for path in paths:
            modify_line_path(path)


def get_path_category(d_attr: str):
    """
    分类函数：
    1: ML  + 整数 -> 直线
    2: ML  + 小数 -> 星号
    3: MCz + 小数 -> 点圆
    """
    d_attr = d_attr[0:100]  # 只看前100字符
    # 第一步：只要包含曲线，直接返回 3
    if "C" in d_attr:
        return 3
    # 匹配规则：带小数点，直接返回 2
    if "." in d_attr:
        return 2
    # 第三步：没有小数、没有曲线 → 纯整数直线 → 返回 1
    return 1


def clip_line_to_square(x1, y1, x2, y2, size=73):
    # 移除默认参数，简化判断
    if x1 == x2 and y1 == y2:
        return []
    points = []
    if x1 == x2:
        if 0 <= x1 <= size:
            return [(x1, 0.0), (x1, size)]
        return []

    k = (y2 - y1) / (x2 - x1)
    b = y1 - k * x1

    # x=0
    y = b
    if 0 <= y <= size:
        points.append((0.0, y))
    # x=size
    y = k * size + b
    if 0 <= y <= size:
        points.append((size, y))
    # y=0
    if k != 0:
        x = -b / k
        if 0 <= x <= size:
            points.append((x, 0.0))
        # y=size
        x = (size - b) / k
        if 0 <= x <= size:
            points.append((x, size))

    # 简化去重逻辑，无排序+快速判断
    if len(points) < 2:
        return []
    return [points[0], points[-1]]


def modify_path_extend_clip(soup: BeautifulSoup):
    for path in soup.select('pattern[patternUnits="userSpaceOnUse"] path'):
        # --- 1. 获取基础数据 ---
        d_attr = str(path.get("d", ""))
        style_attr = str(path.get("style", ""))

        # 提取当前 path 下所有的数字坐标
        all_coords = list(map(float, re.findall(r"[-+]?\d*\.?\d+", d_attr)))
        if not all_coords:
            continue
        f = all_coords

        # 预处理 style：修改 linecap
        style_attr = style_attr.replace(
            "stroke-linecap: butt", "stroke-linecap: square"
        )

        category = get_path_category(d_attr)

        # 类别 1: 线段逻辑
        if category == 1:
            new_d = []
            for i in range(0, len(f) - 3, 4):
                if clipped := clip_line_to_square(f[i], f[i + 1], f[i + 2], f[i + 3]):
                    (nx1, ny1), (nx2, ny2) = clipped
                    new_d.append(f"M {nx1:.3f} {ny1:.3f} L {nx2:.3f} {ny2:.3f}")
            if new_d:
                path["d"] = " ".join(new_d)
                # 清洗 style 里的 fill 并设置 fill 属性
                path["style"] = re.sub(r"fill\s*:\s*[^;]+;?", "", style_attr).strip()
                path["fill"] = "none"
            continue

        # 3: 圆圈替换 + G 标签包裹
        elif category == 3:
            sub_paths = re.findall(r"(M[^Mz]+z)", d_attr)
            unique_circles = {}
            for sub_d in sub_paths:
                sub_f = list(map(float, re.findall(r"[-+]?\d*\.?\d+", sub_d)))
                if not sub_f:
                    continue
                sub_xs, sub_ys = sub_f[0::2], sub_f[1::2]
                rel_cx = (min(sub_xs) + max(sub_xs)) / 2
                rel_cy = (min(sub_ys) + max(sub_ys)) / 2
                r = max(max(sub_xs) - min(sub_xs), max(sub_ys) - min(sub_ys)) / 2
                key = (round(rel_cx, 2), round(rel_cy, 2))
                if key not in unique_circles or r > unique_circles[key]:
                    unique_circles[key] = r
            if not unique_circles:
                continue
            # 创建 <g> 容器
            g_tag = soup.new_tag("g")

            # --- 提取并清洗通用样式到 g 标签 ---
            # 移除 fill 声明，将 linecap 设为 round
            clean_style = re.sub(r"fill\s*:\s*[^;]+;?", "", style_attr).strip()
            clean_style = clean_style.replace(
                "stroke-linecap: square", "stroke-linecap: round"
            )
            if clean_style and not clean_style.endswith(";"):
                clean_style += ";"
            g_tag["style"] = clean_style
            g_tag["fill"] = "none"
            for (cx, cy), r in unique_circles.items():
                c = soup.new_tag("circle")
                c["cx"] = f"{cx:.3f}"
                c["cy"] = f"{cy:.3f}"
                c["r"] = f"{r:.3f}"
                g_tag.append(c)
            path.insert_before(g_tag)
            path.decompose()
