import re
from bs4 import BeautifulSoup, Tag
from math import hypot


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


def clip_line_to_square(x1, y1, x2, y2, size=73):
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
    if len(points) < 2:
        return []
    return [points[0], points[-1]]


def parse_path(d):
    """
    解析并识别 ring, circle, line, star。
    特别逻辑：识别连续的两个 circle 是否组成 ring。
    """
    path_list = []
    segments = [p for p in d.split("M")]
    for s in segments:
        if not s:
            continue
        l_count = 0
        has_c = False
        for ch in s:
            if ch == "L":
                l_count += 1
                if l_count > 1:
                    break  # 提前结束
            elif ch == "C":
                has_c = True
                break  # 直接判 circle，无需再扫
        if has_c:
            name = "circle"
            s = "M" + s
        elif l_count == 1:
            name = "line"
            s = "M" + s
        else:
            name = "star"
            s = "M" + s + "z"
        path_list.append({"name": name, "str": s.strip()})

    raw_elements = []
    for s in path_list:
        if s["name"] == "circle":
            coords = [float(x) for x in re.findall(r"[-+]?\d*\.?\d+", s["str"])]
            xs, ys = coords[0::2], coords[1::2]
            if xs and ys:
                cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
                r = (max(xs) - min(xs)) / 2
                raw_elements.append({"name": "circle", "center": (cx, cy), "r": r})
        elif s["name"] == "line":
            coords = [float(x) for x in re.findall(r"[-+]?\d*\.?\d+", s["str"])]
            raw_elements.append({"name": "line", "coords": coords[:4]})
        else:
            raw_elements.append({"name": "star", "str": s["str"]})

    # 2. 识别连续的环 (Ring)
    final_list = []
    i = 0
    while i < len(raw_elements):
        curr = raw_elements[i]
        # 如果当前和下一个都是 circle，检查是否成环
        if (
            i + 1 < len(raw_elements)
            and curr["name"] == "circle"
            and raw_elements[i + 1]["name"] == "circle"
        ):
            next_el = raw_elements[i + 1]
            success, ring_data = is_ring(
                curr["center"], curr["r"], next_el["center"], next_el["r"]
            )
            if success:
                final_list.append({"name": "ring", "data": ring_data})
                i += 2  # 跳过已合并的两个圆
                continue
        final_list.append(curr)
        i += 1
    return final_list


def is_ring(c1, r1, c2, r2, eps=1e-2):
    """判断两个圆是否构成环，返回 (bool, data)"""
    # 计算圆心之间的距离
    center_dist = hypot(c1[0] - c2[0], c1[1] - c2[1])
    if center_dist > eps:
        return False, None  # 如果圆心距离较大，则不是环
    # 判断半径是否差异较小
    if abs(r1 - r2) < eps:
        return False, None  # 半径差异不明显，则不是环
    # 计算外圆和内圆的半径
    r_big = max(r1, r2)
    r_small = min(r1, r2)
    # 判断圆是否满足环的条件（同心且一个圆包含另一个圆）
    if center_dist + r_small <= r_big + eps:
        r_mid = 0.5 * (r1 + r2)  # 取中间半径
        line_width = abs(r1 - r2)  # 计算线宽
        return True, {"center": c1, "r_outer": r_mid, "line_width": line_width}
    return False, None


def modify_path_extend_clip(soup: BeautifulSoup):

    for path in soup.select('pattern[patternUnits="userSpaceOnUse"] path'):
        d_attr = str(path.get("d", ""))
        style_attr = str(path.get("style", ""))

        elements = parse_path(d_attr)

        # 初始化容器
        g_tag_for_circles = soup.new_tag("g")
        g_tag_for_circles["style"] = style_attr

        has_circles = False
        lines_d = []
        stars_d = []

        for el in elements:
            # --- 1. 处理圆/环 (放入 G 标签) ---
            if el["name"] == "ring":
                data = el["data"]
                r_tag = soup.new_tag("circle")
                r_tag["cx"] = f"{data['center'][0]:.3f}"
                r_tag["cy"] = f"{data['center'][1]:.3f}"
                r_tag["r"] = f"{data['r_outer']:.3f}"
                r_tag["fill"] = "none"
                g_tag_for_circles.append(r_tag)
                has_circles = True

            elif el["name"] == "circle":
                c_tag = soup.new_tag("circle")
                c_tag["cx"] = f"{el['center'][0]:.3f}"
                c_tag["cy"] = f"{el['center'][1]:.3f}"
                c_tag["r"] = f"{el['r']:.3f}"
                # c_tag["fill"] = original_fill
                g_tag_for_circles.append(c_tag)
                has_circles = True

            # --- 2. 收集直线 (准备独立 path) ---
            elif el["name"] == "line":
                coords = el["coords"]
                if len(coords) >= 4:
                    clipped = clip_line_to_square(
                        coords[0], coords[1], coords[2], coords[3]
                    )
                    if clipped:
                        (nx1, ny1), (nx2, ny2) = clipped[:2]
                        lines_d.append(f"M {nx1:.3f} {ny1:.3f} L {nx2:.3f} {ny2:.3f}")

            # --- 3. 收集星号 (留在原 path) ---
            elif el["name"] == "star":
                stars_d.append(el["str"])

        # --- 插入逻辑 ---

        # 如果有圆，插入 G 标签
        if has_circles:
            path.insert_before(g_tag_for_circles)

        # 如果有直线，插入独立 path (带 style)
        if lines_d:
            l_path = soup.new_tag("path")
            l_path["d"] = " ".join(lines_d)
            l_path["style"] = style_attr.replace(
                "stroke-linecap: butt", "stroke-linecap: square"
            )
            path.insert_before(l_path)

        # 处理原 path (星号保留)
        if stars_d:
            path["d"] = " ".join(stars_d)
        else:
            path.decompose()
