from bs4 import BeautifulSoup, Tag
from matplotlib.pyplot import gcf
import copy
import io
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from visioplot.visiolib import VisioExporter


class Fig:
    def __init__(self, fig):
        self.fig: Figure = copy.deepcopy(fig)

    def savefig(self, *args, **kwargs) -> VisioExporter:
        kwargs["format"] = "svg"
        fig = self.fig
        ax = fig.get_axes()[0]
        svg_buffer = io.BytesIO()
        fig.savefig(svg_buffer, **kwargs)
        svg_buffer.seek(0)
        svg_content = svg_buffer.read()

        cleaned_svg_window, flag_out = _svg_windows(svg_content)

        if flag_out is False:
            combined_svg_content = cleaned_svg_window
        else:
            bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
            ax.set_axis_off()
            legend = ax.get_legend()
            if legend:
                legend.remove()
            kwargs["bbox_inches"] = bbox
            svg_buffer = io.BytesIO()
            fig.savefig(svg_buffer, **kwargs)
            svg_buffer.seek(0)
            svg_content = svg_buffer.read()
            svg_content = _svg_content(svg_content)
            combined_svg_content = _combined_svg(cleaned_svg_window, svg_content)
        combined_svg_content = _svg_clean(combined_svg_content)
        combined_svg_content = modify_axis(str(combined_svg_content))
        plt.close(fig)
        fname = Path(args[0]).with_suffix(".svg")
        with open(fname, "w", encoding="utf-8") as file:
            file.write(combined_svg_content)
        return VisioExporter(fname)


def savefig(*args, **kwargs) -> VisioExporter:
    fig = gcf()
    return Fig(fig).savefig(*args, **kwargs)


def _svg_clean(svg_content):
    soup = BeautifulSoup(svg_content, "xml")
    for metadata_tag in soup.find_all("metadata"):
        metadata_tag.decompose()
    for style_tag in soup.find_all("style"):
        style_tag.decompose()
    for tag in soup.find_all(True):
        if "clip-path" in tag.attrs:
            del tag["clip-path"]
    for g_tag in soup.find_all("g"):
        if g_tag.get("id") == "ax":
            continue
        g_id = g_tag.get("id") or ""
        has_relevant_id = any(
            k in g_id for k in ["legend", "figure", "axes"]
        )
        has_single_child = len(g_tag.find_all()) <= 1
        if has_relevant_id or has_single_child:
            g_tag.unwrap()
    return soup.prettify()


def _svg_windows(svg_content):
    soup = BeautifulSoup(svg_content, "xml")
    flag_out = False
    for g_tag in soup.find_all("g", id="out"):
        path_tag_tmp = Tag(name="path")
        defs_tag = Tag(name="defs")
        for path_tag in g_tag.find_all("path"):
            if path_tag.get("id") is not None:
                path_tag_tmp = path_tag.copy_self()
                defs_tag.append(path_tag_tmp)
                break
        g_tag.replace_with(defs_tag)
        flag_out = True
    return soup.prettify(), flag_out


def _svg_content(svg_content):
    soup = BeautifulSoup(svg_content, "xml")
    svg_root = soup.find("svg")
    if svg_root is None:
        return str(soup)
    viewbox_attr = svg_root.get("viewBox") or "0 0 0 0"
    viewbox = str(viewbox_attr).split()
    width = float(viewbox[2])
    height = float(viewbox[3])
    out_elements = soup.find_all("g", id="out")
    out_point_defs_id = []
    svg_root.clear()
    if len(out_elements) == 0:
        return str(soup)
    for out_element in out_elements:
        for path_tag in out_element.find_all("path"):
            if path_tag.get("clip-path") is not None:
                modify_line_path(path_tag)
            path_tag.get("id", "")
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
    return str(soup)


def _combined_svg(window, content):
    window_soup = BeautifulSoup(window, "xml")
    content_soup = BeautifulSoup(content, "xml")
    clip_path_tag = window_soup.find("clipPath")
    if clip_path_tag is None:
        return window_soup.prettify()
    rect_tag = clip_path_tag.find("rect")
    if rect_tag is None:
        return window_soup.prettify()
    ax_tag = content_soup.find("g", id="ax")
    if ax_tag:
        rect_x = rect_tag.get("x") or "0"
        rect_y = rect_tag.get("y") or "0"
        ax_tag.attrs["transform"] = f"translate({rect_x}, {rect_y})"
        axes_tag = window_soup.find("g", {"id": "axes_1"})
        if axes_tag is not None:
            axes_tag.insert(2, ax_tag)
    return window_soup.prettify()


def modify_line_path(path_element):
    if path_element.name != "path":
        path_element = path_element.find("path")
    points = path_element.get("d").split()
    num_points = int(len(points) / 3)
    points = [point for point in points if point not in ("M", "L", "z")]

    if len(points) % 2 != 0:
        raise ValueError(
            "The number of points is not even, cannot form valid line segments."
        )
    style = path_element.get("style", "")
    if "stroke-linecap" in style:
        style = style.replace("stroke-linecap: square", "stroke-linecap: round")
    else:
        style += "stroke-linecap: round;"
    g = Tag(name="g")
    g["clip-path"] = path_element.get("clip-path")
    g["style"] = style
    g["id"] = "line-id"

    for i in range(0, num_points - 1):
        x1, y1, x2, y2 = points[2 * i : 2 * i + 4]
        line = Tag(name="line")
        line["x1"] = x1
        line["y1"] = y1
        line["x2"] = x2
        line["y2"] = y2
        g.append(line)

    path_element.replace_with(g)
    return g


def modify_axis(content: str):
    """
    修改指定坐标轴的路径为线段,只能结合axisartist一起使用
    """
    soup = BeautifulSoup(content, "xml")
    svg_root = soup.find("svg")
    if svg_root is None:
        return str(soup)
    axis_id_list = [
        "mpl_toolkits.axisartist.axis_artist_1",
        "mpl_toolkits.axisartist.axis_artist_2",
        "mpl_toolkits.axisartist.axis_artist_3",
        "mpl_toolkits.axisartist.axis_artist_4",
    ]
    for g_tag in svg_root.find_all("g"):
        if g_tag.get("id") in axis_id_list:
            for axis_path_tag in g_tag.find_all("path"):
                if axis_path_tag.get("id") is None:
                    modify_line_path(axis_path_tag)
    return str(soup)

