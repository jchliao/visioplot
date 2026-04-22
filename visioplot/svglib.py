import copy
import io
from pathlib import Path
from bs4 import BeautifulSoup, Tag
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.pyplot import gcf
from visioplot.visiolib import VisioExporter
from visioplot.svg_utils import (
    modify_line_path,
    modify_axis,
    modify_path_extend_clip,
    modify_mathtext,
    AXIS_ID_LIST,
)


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
        modify_mathtext(main_soup)
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
    if style := soup.find("style"):
        style.string = "path {stroke-linejoin:round;stroke-linecap:square}"
    for useless_tag in soup.find_all(["metadata", "clipPath"]):
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
    for path_tag in soup.find_all("path", id=True):
        if style := path_tag.get("style", ""):
            style = f"{str(style).rstrip(';')}; stroke-linecap: butt"
        else:
            style = "stroke-linecap: butt"
        path_tag["style"] = style


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
