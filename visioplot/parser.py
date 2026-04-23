import re
from visioplot.debug_utils import debug_print
from visioplot.constants import visPosNormal, visPosSuper, visPosSub

SUGAR_PATTERN = re.compile(r"([_^])(\*{1,3})(.*?)\2", flags=re.DOTALL)


def _normalize_syntax_sugar(text: str) -> str:
    """
    把所有上下标语法糖统一转为标准 LaTeX 格式：
    _*abc*     → _{*abc*}
    _**abc**   → _{**abc**}
    _***abc*** → _{***abc***}
    ^*abc*     → ^{*abc*}
    支持嵌套、支持跨多行
    """

    def replace_match(match):
        sym, marker, content = match.groups()
        return f"{sym}{{{marker}{content}{marker}}}"

    normalized, _ = SUGAR_PATTERN.subn(replace_match, text)
    return normalized


def _core_parse(text: str) -> list:
    """
    核心解析：只处理标准格式
    * ** *** 粗斜体
    _{ }  ^{ }  单字 上下标
    自动继承样式、支持无限嵌套
    """
    segments = []
    i = 0
    n = len(text)
    active_bold = False
    active_italic = False

    def push(seg_text, pos, it, bd):
        if not seg_text:
            return
        if segments:
            last_text, last_pos, last_it, last_bd = segments[-1]
            if last_pos == pos and last_it == it and last_bd == bd:
                segments[-1] = (last_text + seg_text, pos, it, bd)
                return
        segments.append((seg_text, pos, it, bd))

    while i < n:
        c = text[i]

        if c == "*":
            if text.startswith("***", i):
                active_bold = not active_bold
                active_italic = not active_italic
                i += 3
            elif text.startswith("**", i):
                active_bold = not active_bold
                i += 2
            else:
                active_italic = not active_italic
                i += 1
            continue

        if c in ("_", "^"):
            mode = visPosSub if c == "_" else visPosSuper
            i += 1
            if i >= n:
                break

            if text[i] == "{":
                i += 1
                start = i
                brace = 1
                while i < n and brace > 0:
                    if text[i] == "{":
                        brace += 1
                    elif text[i] == "}":
                        brace -= 1
                    i += 1
                content = text[start : i - 1]
                sub_segs = _core_parse(content)
                for t, _, it, bd in sub_segs:
                    push(t, mode, it or active_italic, bd or active_bold)
                continue

            push(text[i], mode, active_italic, active_bold)
            i += 1
            continue
        start = i
        while i < n and text[i] not in "*_^":
            i += 1
        push(text[start:i], visPosNormal, active_italic, active_bold)
    return segments


def parse_latex_like(text: str) -> list:
    """完整版类 LaTeX 解析器（分层架构）"""
    if not text:
        return []

    debug_print(f"parse_latex_like: 原始文本='{text}'")
    normalized = _normalize_syntax_sugar(text)
    debug_print(f"parse_latex_like: 规范化后='{normalized}'")

    segments = _core_parse(normalized)
    debug_print(f"parse_latex_like: 完成，segments={len(segments)}")
    return segments
