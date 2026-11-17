# -*- coding: utf-8 -*-
"""
图章生成器 · 桌面版（Python + Pillow）

设计原则（与 Web 版《图章生成器.html》保持一致）：
  · 参数模型逐字段相同，JSON 可直接互换，见 参数模型约定.md
  · 内部尺寸统一用毫米(mm)，渲染时乘以 px/mm 换算
  · 环排角度  a_i = (startAngle + i * stepAngle) mod 360
  · 五角星内径比 r = R * sin18° / sin54° ≈ 0.38197
  · 每个文本对象独立设置字体 / 加粗 / 字号 / 颜色；默认字体为「宋体」

两个版本改一处就要同步改另一处，函数名与常量名尽量一一对应。
"""

import json
import math
import os
import sys
import tkinter as tk
try:
    import customtkinter as ctk
except Exception:
    raise SystemExit("缺少依赖 customtkinter，请先运行：\n"
                     "  pip install customtkinter\n"
                     "（渲染本身只需 Pillow，界面美化用的是 customtkinter）")
from tkinter import ttk, filedialog, colorchooser, messagebox

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageTk

APP_TITLE = "图章生成器 · 桌面版"
GOLD = math.sin(math.pi / 10) / math.sin(3 * math.pi / 10)   # 0.38197…

# ---------------------------------------------------------------- 字体表
FONT_DIR = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")

FONT_FILES = {
    "宋体":      "simsun.ttc",
    "新宋体":    "simsunb.ttf",
    "黑体":      "simhei.ttf",
    "楷体":      "simkai.ttf",
    "仿宋":      "simfang.ttf",
    "微软雅黑":  "msyh.ttc",
    "等线":      "Deng.ttf",
    "华文中宋":  "STZHONGS.TTF",
    "华文行楷":  "STXINGKA.TTF",
    "华文隶书":  "STLITI.TTF",
    "隶书":      "SIMLI.TTF",
}
# 有真粗体文件的字体才用真粗体，其余用描边模拟（效果更可控）
FONT_BOLD_FILES = {
    "微软雅黑": "msyhbd.ttc",
    "等线":     "Dengb.ttf",
}
FONT_NAMES = list(FONT_FILES.keys())
DEFAULT_FONT = "宋体"

PRESET_COLORS = ["#d0021b", "#c62828", "#b71c1c", "#1b3a8f", "#1f5c3a", "#2b2b2b"]


def font_path(name, custom=""):
    """解析字体名 -> 字体文件绝对路径，找不到时退回宋体。"""
    custom = (custom or "").strip()
    if custom:
        if os.path.isfile(custom):
            return custom
        guess = os.path.join(FONT_DIR, custom)
        if os.path.isfile(guess):
            return guess
        if os.path.isfile(guess + ".ttf"):
            return guess + ".ttf"
    f = FONT_FILES.get(name) or FONT_FILES[DEFAULT_FONT]
    p = os.path.join(FONT_DIR, f)
    if os.path.isfile(p):
        return p
    p = os.path.join(FONT_DIR, FONT_FILES[DEFAULT_FONT])
    return p if os.path.isfile(p) else ""


_font_cache = {}


def load_font(name, size_px, bold=False, custom=""):
    """带缓存的字体加载；size_px 为像素高度。"""
    size_px = max(4, int(round(size_px)))
    key = (name, size_px, bold, custom)
    if key in _font_cache:
        return _font_cache[key]
    path = font_path(name, custom)
    real_bold = False
    if bold and name in FONT_BOLD_FILES:
        bp = os.path.join(FONT_DIR, FONT_BOLD_FILES[name])
        if os.path.isfile(bp):
            path, real_bold = bp, True
    try:
        f = ImageFont.truetype(path, size_px) if path else ImageFont.load_default()
    except Exception:
        f = ImageFont.load_default()
    _font_cache[key] = (f, real_bold)
    return _font_cache[key]


# ---------------------------------------------------------------- 纹理
# 画笔纹理：只调制墨迹覆盖度（alpha），颜色仍由对象自身的 color 决定。
# 内置纹理为程序化生成，算法与 Web 版逐位一致；外部纹理来自 纹理/ 目录下的 PNG。


def app_dir():
    """程序所在目录。

    源码直跑 = 脚本目录；打包成 exe 后 = exe 所在目录。
    onefile 模式下 __file__ 指向临时解压目录（每次启动都换），
    若用它算路径，「纹理」文件夹会跑到 temp 里，用户在 exe 旁边放 PNG 也读不到。
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


TEX_DIR = os.path.join(app_dir(), "纹理")
TEX_SIZE = 128
TEX_SEED = 20241117
BUILTIN_TEX = [("noise", "斑驳"), ("fine", "细颗粒"), ("stripe", "斜纹"), ("dot", "网点")]

TEX_FILES = {}      # 纹理名 -> 文件路径（启动时扫描 纹理/ 目录）


def scan_textures():
    TEX_FILES.clear()
    try:
        if not os.path.isdir(TEX_DIR):
            os.makedirs(TEX_DIR, exist_ok=True)
        for fn in sorted(os.listdir(TEX_DIR)):
            if fn.lower().endswith((".png", ".webp", ".jpg", ".jpeg")):
                TEX_FILES[os.path.splitext(fn)[0]] = os.path.join(TEX_DIR, fn)
    except Exception:
        pass


def make_tex_image(tid):
    n = TEX_SIZE
    img = Image.new("RGBA", (n, n))
    px = img.load()
    s = TEX_SEED
    for y in range(n):
        for x in range(n):
            a = 255
            if tid in ("noise", "fine"):
                s = (s * 1103515245 + 12345) & 0xFFFFFFFF
                v = ((s >> 16) & 0xFF) / 255.0
                t = v * v * v if tid == "noise" else v * v * v * v * v
                a = int(round(255 - t * (220 if tid == "noise" else 180)))
            elif tid == "stripe":
                a = 255 if ((x + y) % 14) < 10 else 60
            elif tid == "dot":
                dx, dy = (x % 9) - 4, (y % 9) - 4
                a = 255 if dx * dx + dy * dy <= 6 else 120
            px[x, y] = (255, 255, 255, a)
    return img


_tex_cache = {}


def get_texture(tid):
    """纹理 id -> PIL RGBA 图像；找不到返回 None。"""
    if not tid:
        return None
    tid = str(tid)
    if tid in _tex_cache:
        return _tex_cache[tid]
    builtin = dict(BUILTIN_TEX)
    if tid in builtin.values():
        tid = [k for k, v in BUILTIN_TEX if v == tid][0]
    if tid in dict(BUILTIN_TEX):
        im = make_tex_image(tid)
    else:
        path = TEX_FILES.get(tid) or os.path.join(TEX_DIR, tid + ".png")
        if not os.path.isfile(path):
            return None
        try:
            im = Image.open(path).convert("RGBA")
        except Exception:
            return None
    _tex_cache[tid] = im
    return im


_tile_cache = {}


def _tile_alpha(tex, key, nw, nh):
    """纹理缩放到目标尺寸后取 alpha 通道；尺寸不变时直接复用，省掉重复缩放。"""
    ck = (key, nw, nh)
    hit = _tile_cache.get(ck)
    if hit is not None:
        return hit
    ta = tex.resize((nw, nh), Image.LANCZOS).getchannel("A")
    if len(_tile_cache) > 48:
        _tile_cache.clear()
    _tile_cache[ck] = ta
    return ta


def apply_texture(layer, tex, tile_px, opacity=1.0, key="", phase=(0, 0)):
    """把纹理作为 alpha 遮罩叠到图层上（平铺，tile_px = 每块纹理的像素宽）。

    phase 是该图层在整幅画布中的左上角坐标。平铺起点按它取模对齐，
    这样无论图层是从整图裁出来的哪一块，纹理相位都与整图从原点平铺时一致。
    """
    w, h = layer.size
    if w <= 0 or h <= 0 or tile_px <= 0 or tex is None:
        return
    tw, th = tex.size
    nw = max(1, int(round(tile_px)))
    nh = max(1, int(round(tile_px * th / max(1, tw))))
    ta = _tile_alpha(tex, key or id(tex), nw, nh)
    mask = Image.new("L", (w, h), 255)
    ox, oy = int(phase[0]), int(phase[1])
    for y in range(-(oy % nh), h, nh):
        for x in range(-(ox % nw), w, nw):
            mask.paste(ta, (x, y))
    try:
        op = float(opacity)
    except Exception:
        op = 1.0
    if op < 1.0:
        op = max(0.0, min(1.0, op))
        mask = mask.point(lambda v: int(round(255 - (255 - v) * op)))
    layer.putalpha(ImageChops.multiply(layer.getchannel("A"), mask))


# ---------------------------------------------------------------- 参数模型
def default_text(i):
    base = {
        "visible": False, "content": "", "font": DEFAULT_FONT, "fontCustom": "",
        "bold": False, "size": 6.5, "stretch": 1.0, "spacing": 0.6,
        "mode": "ring", "radius": 15.5, "startAngle": 0.0, "stepAngle": 25.0,
        "autoStep": False, "arcSpan": 0.0, "inward": False, "dx": 0.0, "dy": 0.0,
        "color": "#d0021b", "texture": "", "textureScale": 8.0, "textureOpacity": 1.0,
    }
    if i == 0:
        base.update(visible=True, content="示例网络科技有限公司", size=5.6,
                    radius=15.2, startAngle=-103.5, stepAngle=23.0, spacing=0.0)
    if i == 1:
        base.update(visible=True, content="编号 0000001", mode="flat",
                    size=3.4, dy=15.0, spacing=0.15)
    if i == 2:
        base.update(visible=False, content="", mode="flat", size=4.0, dy=-13.0)
    return base


def default_params():
    return {
        "design": {"margin": 8.0, "linkScale": True},
        "frame": {"visible": True, "shape": "circle", "w": 40.0, "h": 40.0,
                  "stroke": 1.2, "color": "#d0021b",
                  "texture": "", "textureScale": 8.0, "textureOpacity": 1.0},
        "inner": {"visible": False, "w": 34.0, "h": 34.0,
                  "stroke": 0.5, "color": "#d0021b",
                  "texture": "", "textureScale": 8.0, "textureOpacity": 1.0},
        "axis": {"visible": False, "w": 26.0, "h": 0.8, "stroke": 0.8,
                 "dx": 0.0, "dy": 9.0, "color": "#d0021b",
                 "texture": "", "textureScale": 8.0, "textureOpacity": 1.0},
        "symbol": {"visible": True, "kind": "star5", "radius": 6.4, "ratio": GOLD,
                   "dx": 0.0, "dy": 0.0, "color": "#d0021b", "img": None,
                   "texture": "", "textureScale": 8.0, "textureOpacity": 1.0},
        "texts": [default_text(0), default_text(1), default_text(2)],
        "out": {"dpi": 300},
    }


def get_path(P, path):
    cur = P
    for k in path.split("."):
        cur = cur[int(k)] if k.isdigit() else cur[k]
    return cur


def set_path(P, path, value):
    ks = path.split(".")
    cur = P
    for k in ks[:-1]:
        cur = cur[int(k)] if k.isdigit() else cur[k]
    last = ks[-1]
    if last.isdigit():
        cur[int(last)] = value
    else:
        cur[last] = value


def scale_content(P, k):
    """等比缩放「内容」：位置、尺寸、线宽都乘同一个系数。

    线宽也缩放——只缩几何不缩线宽的话，10mm 的小章上 1.2mm 的圆环会变成甜甜圈。
    不缩放的三类：外框宽高（它是缩放的驱动）、留白（纸边距）、DPI。
    与 Web 版 scaleContent() 逐字段对应。
    """
    if not k or abs(k - 1.0) < 1e-12:
        return

    def mul(obj, keys):
        for key in keys:
            v = obj.get(key)
            if isinstance(v, (int, float)):
                # 保留 6 位：避免 JSON 出现 20.400000000000002 这类尾巴，也不影响可逆性
                obj[key] = round(v * k, 6)

    mul(P["frame"], ["stroke", "textureScale"])
    mul(P["inner"], ["w", "h", "stroke", "textureScale"])
    mul(P["axis"], ["w", "h", "stroke", "dx", "dy", "textureScale"])
    mul(P["symbol"], ["radius", "dx", "dy", "textureScale"])
    for t in P["texts"]:
        mul(t, ["size", "radius", "spacing", "dx", "dy", "textureScale"])


def design_box(P):
    """画布尺寸只由外框决定（原程序说明：图形的最终输出大小按外线设置）。

    · 以前把内框也算进 max()：内框比外框大、或内框线宽为 0 时，画布会被撑大却没有内容
    · 圆章只有一个尺寸——宽度即直径，高度不参与；否则改高度会把圆压小
    · 留白 0 合法，只有缺失/非法才回落 8
    """
    try:
        m = float(P["design"]["margin"])
    except (TypeError, ValueError):
        m = 8.0
    fw = float(P["frame"]["w"])
    fh = fw if P["frame"]["shape"] == "circle" else float(P["frame"]["h"])
    w, h = max(fw, 1.0), max(fh, 1.0)
    return {"w": w + m * 2, "h": h + m * 2, "cx": (w + m * 2) / 2,
            "cy": (h + m * 2) / 2, "m": m}


def hex_rgba(h, a=255):
    h = (h or "#000000").lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    try:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)
    except Exception:
        return (0, 0, 0, a)


def star_vertices(cx, cy, R, ratio, n=5):
    r = R * (ratio if ratio and ratio > 0 else GOLD)
    pts = []
    for k in range(n * 2):
        rad = R if k % 2 == 0 else r
        a = math.radians(-90 + k * 180 / n)
        pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
    return pts


# ---------------------------------------------------------------- 渲染
def draw_frame(d, shape, w, h, cx, cy, sw, color):
    """w/h/sw 均为像素。"""
    if sw <= 0:
        return
    sw = max(1, int(round(sw)))
    if shape == "circle":
        # 圆章：宽度即直径，高度不参与（与 design_box 的取法一致）
        r = w / 2
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=sw)
    elif shape == "ellipse":
        d.ellipse([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], outline=color, width=sw)
    elif shape == "rect":
        d.rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], outline=color, width=sw)
    elif shape == "diamond":
        pts = [(cx, cy - h / 2), (cx + w / 2, cy), (cx, cy + h / 2), (cx - w / 2, cy)]
        d.line(pts + [pts[0]], fill=color, width=sw, joint="curve")
    elif shape == "triangle":
        pts = [(cx + (w / 2) * math.cos(math.radians(-90 + k * 120)),
                cy + (h / 2) * math.sin(math.radians(-90 + k * 120))) for k in range(3)]
        d.line(pts + [pts[0]], fill=color, width=sw, joint="curve")


def _char_layer(ch, font, fill, bold, real_bold, S):
    """把单个字符画到独立图层上（透明底），供旋转使用。

    定位规则（与 Web 版 Canvas 的 textAlign=middle / textBaseline=middle 对齐）：
      · 水平：图层宽 = 该字的前进宽度(advance)，墨迹在 advance 内居中
        —— 若改用墨迹宽度居中，逗号这类偏在一侧的字会整体左移（实测偏差 1.8mm）
      · 垂直：图层高 = ascent+descent 行框，墨迹保持行框内的原始位置
        —— 若改用墨迹高度居中，「一」这类扁字会浮到行中间，不与其它字对齐基线
    """
    probe = Image.new("RGBA", (8, 8))
    pd = ImageDraw.Draw(probe)
    try:
        bb = pd.textbbox((0, 0), ch, font=font, anchor="lt")      # 相对行框左上
    except Exception:
        bb = (0, 0, int(font.size * 0.9), int(font.size))
    try:
        adv = int(round(pd.textlength(ch, font=font)))
    except Exception:
        adv = int(round(bb[2] - bb[0]))
    if ch.strip() == "":
        adv = max(adv, int(font.size * 0.35))
    adv = max(1, adv)
    try:
        ascent, descent = font.getmetrics()
    except Exception:
        ascent, descent = int(font.size), int(round(font.size * 0.25))
    line_h = max(1, ascent + descent)

    sw = 0
    if bold and not real_bold:
        sw = max(1, int(round(font.size * 0.020)))
    # 内边距只需容下描边与抗锯齿边缘；过大只会让旋转变慢（旋转量与图层面积成正比）
    pad = max(2, int(round(font.size * 0.03)) + sw)

    layer = Image.new("RGBA", (adv + pad * 2, line_h + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # 不挪动墨迹在字格内的位置：中文标点（，。：）本来就在字格左下，
    # 强行居中会让它和相邻字的间距忽大忽小
    d.text((pad, pad), ch, font=font, fill=fill, anchor="lt",
           stroke_width=sw, stroke_fill=fill)
    return layer


def render_image(P, ppm, ss=3, transparent=True, fast=None):
    """按 ppm(像素/毫米) 渲染；内部 ss 倍超采样后缩小，得到抗锯齿效果。

    每个绘制对象单独出图层：设了纹理时先画到透明图层，再用纹理遮罩墨迹覆盖度，
    最后合成回主图——与原程序「各对象独立画笔纹理」的行为一致。
    """
    box = design_box(P)
    S = ppm * ss
    W = max(1, int(round(box["w"] * S)))
    H = max(1, int(round(box["h"] * S)))
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0) if transparent else (255, 255, 255, 255))
    cx, cy = box["cx"] * S, box["cy"] * S

    def paint(obj, fn):
        tex = get_texture(obj.get("texture"))
        if tex is None:
            fn(img)
            return
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        fn(layer)
        bb = layer.getbbox()
        if bb is None:
            return
        try:
            scale = float(obj.get("textureScale") or 8)
        except Exception:
            scale = 8.0
        try:
            op = float(obj.get("textureOpacity", 1))
        except Exception:
            op = 1.0
        # 只对墨迹包围盒做遮罩与合成：省掉大量全画布运算，结果与整图处理完全相同
        sub = layer.crop(bb)
        apply_texture(sub, tex, max(1.0, scale * S), op,
                      obj.get("texture") or "", phase=(bb[0], bb[1]))
        img.alpha_composite(sub, dest=(bb[0], bb[1]))

    f = P["frame"]
    if f["visible"]:
        paint(f, lambda t, f=f: draw_frame(ImageDraw.Draw(t), f["shape"], f["w"] * S,
                                           f["h"] * S, cx, cy, f["stroke"] * S,
                                           hex_rgba(f["color"])))

    n = P["inner"]
    if n["visible"]:
        paint(n, lambda t, n=n: draw_frame(ImageDraw.Draw(t), f["shape"], n["w"] * S,
                                           n["h"] * S, cx, cy, n["stroke"] * S,
                                           hex_rgba(n["color"])))

    ax = P["axis"]
    if ax["visible"] and ax["stroke"] > 0:
        paint(ax, lambda t, ax=ax: _draw_axis(t, ax, cx, cy, S))

    sy = P["symbol"]
    if sy["visible"]:
        paint(sy, lambda t, sy=sy: _draw_symbol(t, sy, cx, cy, S))

    for t in P["texts"]:
        if t["visible"]:
            paint(t, lambda layer, tt=t: _draw_text(layer, ImageDraw.Draw(layer),
                                                    tt, cx, cy, S))

    if ss > 1:
        tw_, th_ = max(1, W // ss), max(1, H // ss)
        # fast=None 时按用途自动选：预览(ss<=2)走快速 box 平均，导出走 LANCZOS
        img = _downscale(img, ss, tw_, th_, (ss <= 2) if fast is None else fast)
    return img


def _downscale(img, ss, tw, th, fast=True):
    """超采样图缩回目标尺寸。

    fast=True：crop + reduce（3×3 面积平均），比 LANCZOS 快 4~5 倍。
    fast=False：LANCZOS，笔画边缘略锐，用于导出。两者墨迹范围完全一致。
    """
    if not fast:
        return img.resize((tw, th), Image.LANCZOS)
    try:
        cw, chh = tw * ss, th * ss
        if cw <= img.width and chh <= img.height:
            out = img.crop((0, 0, cw, chh)).reduce(ss) if ss > 1 else img
            if out.size == (tw, th):
                return out
    except Exception:
        pass
    return img.resize((tw, th), Image.LANCZOS)


def _draw_axis(img, ax, cx, cy, S):
    d = ImageDraw.Draw(img)
    px, py = cx + ax["dx"] * S, cy + ax["dy"] * S
    aw, ah = ax["w"] * S, ax["h"] * S
    sw = max(1, int(round(ax["stroke"] * S)))
    color = hex_rgba(ax["color"])
    if ah <= ax["stroke"] * S:
        d.line([px - aw / 2, py, px + aw / 2, py], fill=color, width=sw)
    else:
        d.rectangle([px - aw / 2, py - ah / 2, px + aw / 2, py + ah / 2],
                    outline=color, width=sw)


def _draw_symbol(img, sy, cx, cy, S):
    scx, scy = cx + sy["dx"] * S, cy + sy["dy"] * S
    if sy["kind"] == "image" and sy["img"] and os.path.isfile(str(sy["img"])):
        try:
            im = Image.open(sy["img"]).convert("RGBA")
            dd = sy["radius"] * 2 * S
            im = im.resize((int(dd), int(dd)), Image.LANCZOS)
            img.alpha_composite(im, (int(scx - dd / 2), int(scy - dd / 2)))
            return
        except Exception:
            pass
    d = ImageDraw.Draw(img)
    pts = star_vertices(scx, scy, sy["radius"] * S, sy["ratio"])
    d.polygon(pts, fill=hex_rgba(sy["color"]))


def _draw_text(base, d, t, cx, cy, S):
    if not t["visible"]:
        return
    content = str(t["content"] or "")
    if not content.strip():
        return
    font, real_bold = load_font(t["font"], t["size"] * S, t["bold"], t.get("fontCustom", ""))
    fill = hex_rgba(t["color"])
    chars = list(content)

    if t["mode"] == "ring":
        n = max(1, len(chars))
        step = 360.0 / n if t["autoStep"] else float(t["stepAngle"])
        for i, ch in enumerate(chars):
            deg = float(t["startAngle"]) + i * step
            rad = math.radians(deg)
            x = cx + t["dx"] * S + t["radius"] * S * math.sin(rad)
            y = cy + t["dy"] * S - t["radius"] * S * math.cos(rad)
            layer = _char_layer(ch, font, fill, t["bold"], real_bold, S)
            if float(t["stretch"]) != 1.0:
                layer = layer.resize((max(1, int(layer.width * t["stretch"])), layer.height),
                                     Image.LANCZOS)
            rot = deg + (180 if t["inward"] else 0)
            if abs(rot % 360) > 0.01:
                layer = layer.rotate(-rot, resample=Image.BICUBIC, expand=True)
            base.alpha_composite(layer, (int(x - layer.width / 2), int(y - layer.height / 2)))
    elif t["mode"] == "arc":
        # 弧排：以「起始角度」为弧中心，沿半径 R 铺开。
        # 字符顺序按屏幕左右自动判定，底部文字不必手动反序。
        # 勾选「字头朝内」时字符整体转 180°，字顶朝向圆心。
        n = max(1, len(chars))
        R = max(0.1, float(t["radius"]))
        sp = float(t["spacing"])
        st = float(t["stretch"])
        wid = []
        for ch in chars:
            try:
                w = d.textlength(ch, font=font) / S      # px -> mm
            except Exception:
                w = font.size / S * 0.9
            wid.append(w * st)
        totalW = sum(wid) + sp * (n - 1)
        span = float(t.get("arcSpan", 0) or 0)
        target = math.radians(span) * R if span > 0 else totalW
        k = (target / totalW) if totalW > 0 else 1.0
        a0 = float(t["startAngle"])
        dirSign = 1 if (math.cos(math.radians(a0)) + math.sin(math.radians(a0))) >= 0 else -1
        acc = -target / 2.0
        for i, ch in enumerate(chars):
            wi = wid[i] * k
            s = acc + wi / 2.0
            acc += wi + sp * k
            deg = a0 + dirSign * math.degrees(s / R)
            rad = math.radians(deg)
            x = cx + t["dx"] * S + R * S * math.sin(rad)
            y = cy + t["dy"] * S - R * S * math.cos(rad)
            layer = _char_layer(ch, font, fill, t["bold"], real_bold, S)
            # k<1 表示弧长不够、需要压缩：间距已按 k 排，字形也必须一起压，否则会叠字；
            # k>1 只是把间距拉开，字形保持原宽（拉伸字会变形）
            sc = st * (k if k < 1.0 else 1.0)
            if sc != 1.0:
                layer = layer.resize((max(1, int(layer.width * sc)), layer.height),
                                     Image.LANCZOS)
            rot = deg + (180 if t["inward"] else 0)
            if abs(rot % 360) > 0.01:
                layer = layer.rotate(-rot, resample=Image.BICUBIC, expand=True)
            base.alpha_composite(layer, (int(x - layer.width / 2), int(y - layer.height / 2)))
    else:
        sp = float(t["spacing"]) * S
        st = float(t["stretch"])
        adv = []
        for ch in chars:
            try:
                w = d.textlength(ch, font=font)
            except Exception:
                w = font.size * 0.9
            adv.append(w * st + sp)
        total = sum(adv) - (sp if chars else 0)
        x = cx + t["dx"] * S - total / 2
        y = cy + t["dy"] * S
        for i, ch in enumerate(chars):
            cw = adv[i] - sp
            layer = _char_layer(ch, font, fill, t["bold"], real_bold, S)
            if st != 1.0:
                layer = layer.resize((max(1, int(layer.width * st)), layer.height), Image.LANCZOS)
            base.alpha_composite(layer, (int(x + cw / 2 - layer.width / 2),
                                         int(y - layer.height / 2)))
            x += adv[i]


# ---------------------------------------------------------------- UI
KIND_NUM, KIND_RANGE, KIND_SEL, KIND_TEXT, KIND_CHECK, KIND_SEG, KIND_COLOR, KIND_FONT, KIND_TEX, \
    KIND_PRESET = "num", "range", "sel", "text", "check", "seg", "color", "font", "tex", "preset"

SHAPES = [("circle", "圆章"), ("ellipse", "椭圆章"), ("rect", "方章"),
          ("diamond", "菱形章"), ("triangle", "三角章")]


def text_fields(i):
    p = "texts.%d." % i
    return [
        {"k": KIND_CHECK, "p": p + "visible", "l": "文本 %d" % (i + 1)},
        {"k": KIND_TEXT,  "p": p + "content", "l": "内容"},
        {"k": KIND_FONT,  "p": p + "font", "l": "字体"},
        {"k": KIND_TEXT,  "p": p + "fontCustom", "l": "自定义字体", "ph": "留空用上面的字体"},
        {"k": KIND_CHECK, "p": p + "bold", "l": "加粗"},
        {"k": KIND_RANGE, "p": p + "size", "l": "字号", "u": "mm", "min": 2, "max": 20, "step": 0.1},
        {"k": KIND_RANGE, "p": p + "stretch", "l": "横向缩放", "u": "×", "min": 0.4, "max": 2.5, "step": 0.02},
        {"k": KIND_SEG,   "p": p + "mode", "l": "排列",
         "opts": [("ring", "环排"), ("arc", "弧排·居中"), ("flat", "平排")]},
        {"k": KIND_PRESET, "p": p + "preset", "l": "绕中心排布"},
        {"k": KIND_RANGE, "p": p + "radius", "l": "半径（环/弧）", "u": "mm", "min": 2, "max": 40, "step": 0.1},
        {"k": KIND_NUM,   "p": p + "startAngle", "l": "起始角/弧心", "u": "°", "min": -360, "max": 360, "step": 1},
        {"k": KIND_NUM,   "p": p + "arcSpan", "l": "弧长跨度", "u": "°", "min": 0, "max": 330, "step": 1},
        {"k": KIND_CHECK, "p": p + "autoStep", "l": "均分整圈(环排)"},
        {"k": KIND_NUM,   "p": p + "stepAngle", "l": "每字角度(环排)", "u": "°", "min": -90, "max": 90, "step": 0.5},
        {"k": KIND_CHECK, "p": p + "inward", "l": "字头朝内"},
        {"k": KIND_RANGE, "p": p + "spacing", "l": "字距(平/弧)", "u": "mm", "min": -1, "max": 6, "step": 0.05},
        {"k": KIND_NUM,   "p": p + "dx", "l": "水平位置", "u": "mm", "min": -30, "max": 30, "step": 0.1},
        {"k": KIND_NUM,   "p": p + "dy", "l": "垂直位置", "u": "mm", "min": -30, "max": 30, "step": 0.1},
        {"k": KIND_COLOR, "p": p + "color", "l": "颜色"},
        {"k": KIND_TEX,   "p": p + "texture", "l": "纹理"},
        {"k": KIND_RANGE, "p": p + "textureScale", "l": "纹理缩放", "u": "mm", "min": 1, "max": 40, "step": 0.5},
        {"k": KIND_RANGE, "p": p + "textureOpacity", "l": "纹理浓淡", "u": "", "min": 0, "max": 1, "step": 0.05},
    ]


SECTIONS = [
    ("画布与输出", [
        {"k": "hint", "p": "", "l": "", "t": "尺寸单位 mm；导出像素 = mm ÷ 25.4 × DPI。"},
        {"k": KIND_RANGE, "p": "out.dpi", "l": "导出 DPI", "u": "DPI", "min": 72, "max": 1200, "step": 1},
        {"k": KIND_RANGE, "p": "design.margin", "l": "画布留白", "u": "mm", "min": 0, "max": 30, "step": 1},
        {"k": KIND_CHECK, "p": "design.linkScale", "l": "改外框等比缩放"},
    ]),
    ("纹理库", [
        {"k": "texlib", "p": "", "l": ""},
    ]),
    ("外框", [
        {"k": KIND_CHECK, "p": "frame.visible", "l": "显示"},
        {"k": KIND_SEL,   "p": "frame.shape", "l": "形状", "opts": SHAPES},
        {"k": KIND_RANGE, "p": "frame.w", "l": "宽度/直径", "u": "mm", "min": 10, "max": 80, "step": 0.5},
        {"k": KIND_RANGE, "p": "frame.h", "l": "高度", "u": "mm", "min": 10, "max": 80, "step": 0.5},
        {"k": KIND_RANGE, "p": "frame.stroke", "l": "线宽", "u": "mm", "min": 0, "max": 6, "step": 0.1},
        {"k": KIND_COLOR, "p": "frame.color", "l": "颜色"},
        {"k": KIND_TEX,   "p": "frame.texture", "l": "纹理"},
        {"k": KIND_RANGE, "p": "frame.textureScale", "l": "纹理缩放", "u": "mm", "min": 1, "max": 40, "step": 0.5},
        {"k": KIND_RANGE, "p": "frame.textureOpacity", "l": "纹理浓淡", "u": "", "min": 0, "max": 1, "step": 0.05},
    ]),
    ("内框", [
        {"k": KIND_CHECK, "p": "inner.visible", "l": "显示"},
        {"k": KIND_RANGE, "p": "inner.w", "l": "宽度", "u": "mm", "min": 5, "max": 78, "step": 0.5},
        {"k": KIND_RANGE, "p": "inner.h", "l": "高度", "u": "mm", "min": 5, "max": 78, "step": 0.5},
        {"k": KIND_RANGE, "p": "inner.stroke", "l": "线宽", "u": "mm", "min": 0, "max": 4, "step": 0.1},
        {"k": KIND_COLOR, "p": "inner.color", "l": "颜色"},
        {"k": KIND_TEX,   "p": "inner.texture", "l": "纹理"},
        {"k": KIND_RANGE, "p": "inner.textureScale", "l": "纹理缩放", "u": "mm", "min": 1, "max": 40, "step": 0.5},
        {"k": KIND_RANGE, "p": "inner.textureOpacity", "l": "纹理浓淡", "u": "", "min": 0, "max": 1, "step": 0.05},
    ]),
    ("中心线 / 中心框", [
        {"k": KIND_CHECK, "p": "axis.visible", "l": "显示"},
        {"k": KIND_RANGE, "p": "axis.w", "l": "宽度", "u": "mm", "min": 0, "max": 70, "step": 0.5},
        {"k": KIND_RANGE, "p": "axis.h", "l": "高度", "u": "mm", "min": 0, "max": 40, "step": 0.1},
        {"k": KIND_RANGE, "p": "axis.stroke", "l": "线宽", "u": "mm", "min": 0.1, "max": 4, "step": 0.05},
        {"k": KIND_NUM,   "p": "axis.dx", "l": "水平偏移", "u": "mm", "min": -30, "max": 30, "step": 0.1},
        {"k": KIND_NUM,   "p": "axis.dy", "l": "垂直偏移", "u": "mm", "min": -30, "max": 30, "step": 0.1},
        {"k": KIND_COLOR, "p": "axis.color", "l": "颜色"},
        {"k": KIND_TEX,   "p": "axis.texture", "l": "纹理"},
        {"k": KIND_RANGE, "p": "axis.textureScale", "l": "纹理缩放", "u": "mm", "min": 1, "max": 40, "step": 0.5},
        {"k": KIND_RANGE, "p": "axis.textureOpacity", "l": "纹理浓淡", "u": "", "min": 0, "max": 1, "step": 0.05},
    ]),
    ("图符", [
        {"k": KIND_CHECK, "p": "symbol.visible", "l": "显示"},
        {"k": KIND_SEG,   "p": "symbol.kind", "l": "类型", "opts": [("star5", "五角星"), ("image", "自定义图片")]},
        {"k": KIND_RANGE, "p": "symbol.radius", "l": "半径", "u": "mm", "min": 1, "max": 30, "step": 0.1},
        {"k": KIND_RANGE, "p": "symbol.ratio", "l": "内径比", "u": "", "min": 0.2, "max": 0.9, "step": 0.005},
        {"k": KIND_NUM,   "p": "symbol.dx", "l": "水平偏移", "u": "mm", "min": -30, "max": 30, "step": 0.1},
        {"k": KIND_NUM,   "p": "symbol.dy", "l": "垂直偏移", "u": "mm", "min": -30, "max": 30, "step": 0.1},
        {"k": KIND_COLOR, "p": "symbol.color", "l": "颜色"},
        {"k": KIND_TEX,   "p": "symbol.texture", "l": "纹理"},
        {"k": KIND_RANGE, "p": "symbol.textureScale", "l": "纹理缩放", "u": "mm", "min": 1, "max": 40, "step": 0.5},
        {"k": KIND_RANGE, "p": "symbol.textureOpacity", "l": "纹理浓淡", "u": "", "min": 0, "max": 1, "step": 0.05},
        {"k": "image",    "p": "symbol.img", "l": "图片"},
    ]),
    ("文本 1", text_fields(0)),
    ("文本 2", text_fields(1)),
    ("文本 3", text_fields(2)),
]

# 各分组默认展开状态：与网页版保持一致（画布与外框、文本 1 展开，其余收起）
SECTION_OPEN = {
    "画布与输出": True, "纹理库": False, "外框": True, "内框": False,
    "中心线 / 中心框": False, "图符": False,
    "文本 1": True, "文本 2": False, "文本 3": False,
}


# ---------------------------------------------------------------- 视觉参数（与网页版同一套配色）
PAL = dict(bg="#f5f5f3", panel="#ffffff", line="#e3e2de", txt="#2c2c2a",
           txt2="#6b6a64", accent="#b32b1c", accent2="#8f2317", field="#fbfbfa",
           hint="#8a8880")

# 滚轮额外倍数：CTk 在 Windows 上每格固定滚 int(delta/6)=20 像素（yscrollincrement=1），
# 面板内容高约 2400px、视口约 800px，一格 20px 明显发黏。2 表示再补 2 倍，等效 3 倍速。
WHEEL_EXTRA = 2


class CBool:
    """CTkCheckBox 的取值包装：统一提供 get()/set()，与 refresh_all 的约定一致。"""

    def __init__(self, var, widget):
        self.var = var
        self.w = widget

    def get(self):
        return bool(self.var.get())

    def set(self, v):
        self.var.set(1 if v else 0)


class App:
    def __init__(self, root):
        self.root = root
        self.P = default_params()
        self.vars = {}
        self.tex_combos = []
        self._job = None
        self._loading = False
        self.photo = None
        self._sections = {}

        ctk.set_appearance_mode("light")
        root.title(APP_TITLE)
        root.geometry("1200x820")
        root.minsize(1000, 660)
        try:
            root.configure(fg_color=PAL["bg"])
        except Exception:
            pass

        self.f_title = ctk.CTkFont("Microsoft YaHei", 14, "bold")
        self.f_sec = ctk.CTkFont("Microsoft YaHei", 13, "bold")
        self.f_ui = ctk.CTkFont("Microsoft YaHei", 12)
        self.f_small = ctk.CTkFont("Microsoft YaHei", 11)
        self.f_tiny = ctk.CTkFont("Microsoft YaHei", 10)

        scan_textures()
        self._build_toolbar()
        self._build_status()
        body = ctk.CTkFrame(root, fg_color=PAL["bg"], corner_radius=0)
        body.pack(fill="both", expand=True)

        self._build_panel(body)
        self._build_stage(body)

        self.refresh_all()
        root.after(60, self.redraw)

    # ---------------- 顶部按钮
    def _build_toolbar(self):
        bar = ctk.CTkFrame(self.root, fg_color=PAL["panel"], corner_radius=0, height=54)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        tk.Frame(bar, bg=PAL["line"], height=1).pack(side="bottom", fill="x")

        left = ctk.CTkFrame(bar, fg_color=PAL["panel"], corner_radius=0)
        left.pack(side="left", padx=20, pady=12)
        ctk.CTkLabel(left, text="图章生成器 · 桌面版", font=self.f_title,
                     text_color=PAL["txt"]).pack(side="left")
        ctk.CTkLabel(left, text="Pillow 渲染 · 与 Web 版共用参数模型", font=self.f_small,
                     text_color=PAL["txt2"]).pack(side="left", padx=(12, 0))

        def btn(text, cmd, primary=False, width=88):
            b = ctk.CTkButton(bar, text=text, command=cmd, height=32, width=width,
                              corner_radius=8, font=self.f_small,
                              fg_color=PAL["accent"] if primary else PAL["panel"],
                              hover_color=PAL["accent2"] if primary else "#f2f1ee",
                              text_color="#ffffff" if primary else PAL["txt"],
                              border_width=0 if primary else 1,
                              border_color=PAL["line"])
            b.pack(side="right", padx=(0, 10), pady=11)
            return b

        btn("重置", self.reset)
        btn("载入参数", self.load_json, width=96)
        btn("保存参数", self.save_json, width=96)
        btn("导出 PNG", self.export_png, primary=True, width=100)

    # ---------------- 左侧参数面板
    def _build_panel(self, parent):
        shell = ctk.CTkFrame(parent, fg_color=PAL["panel"], corner_radius=0, width=352)
        shell.pack(side="left", fill="y")
        shell.pack_propagate(False)
        tk.Frame(parent, bg=PAL["line"], width=1).pack(side="left", fill="y")

        panel = ctk.CTkScrollableFrame(shell, fg_color=PAL["panel"], corner_radius=0,
                                       width=330, scrollbar_button_color="#d6d4cd",
                                       scrollbar_button_hover_color="#b9b6ac")
        panel.pack(fill="both", expand=True)
        self.panel = panel
        self.panel_canvas = None
        self._boost_wheel(panel)

        for title, fields in SECTIONS:
            self._section(panel, title, fields)
        ctk.CTkFrame(panel, fg_color=PAL["panel"], height=22, corner_radius=0).pack(fill="x")

    def _boost_wheel(self, panel, extra=WHEEL_EXTRA):
        """给 CTkScrollableFrame 的滚轮提速。

        CTk 的滚轮处理是实例方法 + bind_all 注册好的，改不了它的倍数；
        而 yscrollincrement 也不能动（滚轮单位就是 int(delta/6)，调大反而会失控）。
        所以这里追加一个同序列绑定：CTk 先滚 20px，我们再补滚 extra 倍，等效 3 倍速。
        指针是否在面板内，复用 CTk 自己的 check_if_master_is_canvas()，规则与它完全一致。
        """
        canvas = panel._parent_canvas

        def on_wheel(e):
            try:
                if not panel.check_if_master_is_canvas(e.widget):
                    return
            except Exception:
                return
            step = int(-e.delta / 6) * extra
            if step:
                canvas.yview_scroll(step, "units")

        panel.bind_all("<MouseWheel>", on_wheel, add="+")
        self._wheel_boost = on_wheel          # 供离屏测试直接调用

    def _section(self, parent, title, fields):
        """可折叠分组：标题栏点击展开/收起，默认状态与网页版一致。"""
        opened = SECTION_OPEN.get(title, False)
        sec = ctk.CTkFrame(parent, fg_color=PAL["panel"], corner_radius=0)
        sec.pack(fill="x")

        hd = ctk.CTkFrame(sec, fg_color=PAL["panel"], corner_radius=0, height=32)
        hd.pack(fill="x", padx=10, pady=(6, 0))
        hd.pack_propagate(False)

        # 三角用 Canvas 自绘：▸/▾ 在微软雅黑下缺字形，会显示成横线
        arrow = tk.Canvas(hd, width=12, height=12, bg=PAL["panel"],
                          highlightthickness=0, bd=0, cursor="hand2")
        arrow.pack(side="left", padx=(6, 8), pady=10)

        def draw_arrow(open_):
            arrow.delete("all")
            c = "#9a978e"
            if open_:
                arrow.create_polygon(2, 5, 10, 5, 6, 9, fill=c, outline=c)
            else:
                arrow.create_polygon(4, 3, 4, 11, 8, 7, fill=c, outline=c)

        draw_arrow(opened)
        lbl = ctk.CTkLabel(hd, text=title, font=self.f_sec, text_color=PAL["txt"], anchor="w")
        lbl.pack(side="left")

        body = ctk.CTkFrame(sec, fg_color=PAL["panel"], corner_radius=0)
        for fd in fields:
            self._field(body, fd)

        line = tk.Frame(sec, bg=PAL["line"], height=1)
        if opened:
            body.pack(fill="x", padx=16, pady=(2, 0))
        line.pack(fill="x", pady=(8, 0))

        def toggle(_=None):
            if body.winfo_ismapped():
                body.pack_forget()
                draw_arrow(False)
            else:
                body.pack(fill="x", padx=16, pady=(2, 0), before=line)
                draw_arrow(True)

        for w in (hd, arrow, lbl):
            w.bind("<Button-1>", toggle)
        self._sections[title] = (body, arrow, toggle)

    # ---------------- 控件小工具
    def _row(self, parent, label=None, label_w=86):
        row = ctk.CTkFrame(parent, fg_color=PAL["panel"], corner_radius=0)
        row.pack(fill="x", pady=3)
        if label:
            ctk.CTkLabel(row, text=label, width=label_w, anchor="w",
                         font=self.f_ui, text_color=PAL["txt2"]).pack(side="left")
        return row

    def _small_btn(self, parent, text, cmd, width=112):
        return ctk.CTkButton(parent, text=text, command=cmd, height=26, width=width,
                             corner_radius=7, font=self.f_small,
                             fg_color=PAL["field"], hover_color="#efece6",
                             text_color=PAL["txt"], border_width=1, border_color=PAL["line"])

    def _option_menu(self, parent, names, init_label, command, width=136):
        var = tk.StringVar(value=init_label)
        m = ctk.CTkOptionMenu(parent, values=names, variable=var, width=width, height=28,
                              corner_radius=7, font=self.f_ui,
                              fg_color=PAL["field"], button_color=PAL["field"],
                              button_hover_color="#efece6", text_color=PAL["txt"],
                              dropdown_fg_color="#ffffff", dropdown_text_color=PAL["txt"],
                              dropdown_hover_color="#f2f1ee", dropdown_font=self.f_ui,
                              command=command, dynamic_resizing=False, anchor="w")
        return var, m

    def _seg(self, parent, path, opts, labels):
        """分段按钮：外框 1px + 按钮间 1px，选中红底白字，和网页版 .seg 一致。"""
        holder = ctk.CTkFrame(parent, fg_color=PAL["line"], corner_radius=7)
        holder.pack(side="left", fill="x", expand=True)
        inner = ctk.CTkFrame(holder, fg_color=PAL["line"], corner_radius=7)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        btns = {}
        for i, (v, t) in enumerate(opts):
            b = ctk.CTkButton(inner, text=t, height=26, corner_radius=6, font=self.f_small,
                              width=10, border_width=0,
                              command=lambda vv=v, p=path: self.on_seg(p, vv))
            b.pack(side="left", expand=True, fill="x", padx=(0 if i == 0 else 1, 0))
            btns[v] = b
        self.vars[path] = ("seg", btns)
        return labels

    def _field(self, box, fd):
        k, path, label = fd["k"], fd["p"], fd["l"]

        if k == "hint":
            ctk.CTkLabel(box, text=fd.get("t", ""), font=self.f_small, text_color=PAL["hint"],
                         anchor="w", justify="left", wraplength=296).pack(fill="x", pady=(4, 6))
            return

        if k == "texlib":
            ctk.CTkLabel(box, text="外部纹理：PNG 放进下面这个「纹理」文件夹，启动时自动读取",
                         font=self.f_small, text_color=PAL["hint"], anchor="w",
                         justify="left", wraplength=296).pack(fill="x", pady=(4, 2))
            ctk.CTkLabel(box, text=TEX_DIR, font=self.f_tiny, text_color="#9a978e",
                         anchor="w", justify="left", wraplength=296).pack(fill="x")
            rowb = ctk.CTkFrame(box, fg_color=PAL["panel"], corner_radius=0)
            rowb.pack(fill="x", pady=(6, 4))
            self._small_btn(rowb, "载入纹理 PNG…", self.load_texture, width=132).pack(side="left")
            self._small_btn(rowb, "打开文件夹", self.open_tex_dir).pack(side="left", padx=(8, 0))
            return

        if k == KIND_CHECK:
            var = tk.IntVar(value=1 if get_path(self.P, path) else 0)
            long_label = len(label) > 5          # 长标签独占一行，别把勾选框挤到边上
            row = ctk.CTkFrame(box, fg_color=PAL["panel"], corner_radius=0)
            row.pack(fill="x", pady=3)
            if not long_label:
                ctk.CTkLabel(row, text=label, width=86, anchor="w",
                             font=self.f_ui, text_color=PAL["txt2"]).pack(side="left")
            cb = ctk.CTkCheckBox(row, text=label if long_label else "",
                                 variable=var, onvalue=1, offvalue=0,
                                 width=18, height=18, checkbox_width=17, checkbox_height=17,
                                 corner_radius=4, border_width=2, border_color="#c8c5bc",
                                 fg_color=PAL["accent"], hover_color=PAL["accent2"],
                                 checkmark_color="#ffffff", font=self.f_ui,
                                 text_color=PAL["txt2"],
                                 command=lambda p=path: self.on_change(p))
            # 长标签独占一行，但缩进到与其它行的控件列对齐，勾选框排成一竖列
            cb.pack(side="left", padx=(86 if long_label else 0, 0))
            self.vars[path] = ("bool", CBool(var, cb))
            return

        if k == KIND_PRESET:
            try:
                idx = int(path.split(".")[1])
            except Exception:
                idx = 0
            row = self._row(box, label)
            holder = ctk.CTkFrame(row, fg_color=PAL["line"], corner_radius=7)
            holder.pack(side="left", fill="x", expand=True)
            inner = ctk.CTkFrame(holder, fg_color=PAL["line"], corner_radius=7)
            inner.pack(fill="both", expand=True, padx=1, pady=1)
            for i, (txt, key) in enumerate((("顶部", "top"), ("底部", "bottom"),
                                            ("左侧", "left"), ("右侧", "right"))):
                b = ctk.CTkButton(inner, text=txt, height=26, corner_radius=6, width=10,
                                  font=self.f_small, border_width=0,
                                  fg_color=PAL["field"], hover_color="#efece6",
                                  text_color=PAL["txt2"],
                                  command=lambda k2=key, i2=idx: self.apply_preset(i2, k2))
                b.pack(side="left", expand=True, fill="x", padx=(0 if i == 0 else 1, 0))
            return

        if k == KIND_TEX:
            names = ["（无）"] + [n for _, n in BUILTIN_TEX] + list(TEX_FILES.keys())
            ids = [""] + [i for i, _ in BUILTIN_TEX] + list(TEX_FILES.keys())
            cur = str(get_path(self.P, path) or "")
            row = self._row(box, label)
            var, m = self._option_menu(row, names, names[ids.index(cur)] if cur in ids else "（无）",
                                       lambda val, p=path: self.on_change(p))
            m.pack(side="left")
            self.vars[path] = ("tex", var, ids, names)
            self.tex_combos.append(m)
            return

        if k in (KIND_NUM, KIND_RANGE):
            val = float(get_path(self.P, path))
            step = fd.get("step", 1)
            row = self._row(box, label)
            var = tk.StringVar(value=self._fmt(val, step))
            self.vars[path] = ("num", var, fd)

            def mk_entry(parent):
                e = ctk.CTkEntry(parent, textvariable=var, width=56, height=28,
                                 corner_radius=7, font=self.f_ui,
                                 fg_color=PAL["field"], border_color=PAL["line"],
                                 border_width=1, text_color=PAL["txt"])
                try:
                    e._entry.configure(justify="right")     # CTkEntry 未暴露 justify
                except Exception:
                    pass
                e.bind("<Up>", lambda ev, p=path: self._nudge(p, fd, +1))
                e.bind("<Down>", lambda ev, p=path: self._nudge(p, fd, -1))
                e.bind("<MouseWheel>", lambda ev, p=path: self._nudge(
                    p, fd, 1 if ev.delta > 0 else -1))
                return e

            if k == KIND_RANGE:
                if fd.get("u"):
                    ctk.CTkLabel(row, text=fd["u"], font=self.f_small,
                                 text_color=PAL["txt2"], width=26, anchor="w").pack(side="right")
                mk_entry(row).pack(side="right")
                steps = int(round((float(fd["max"]) - float(fd["min"])) / (step or 1)))
                sl = ctk.CTkSlider(row, from_=fd["min"], to=fd["max"],
                                   number_of_steps=max(1, steps), height=16,
                                   corner_radius=6, button_corner_radius=7,
                                   fg_color="#ddd9d0", progress_color=PAL["accent"],
                                   button_color=PAL["accent"],
                                   button_hover_color=PAL["accent2"], button_length=0,
                                   command=lambda v, p=path, st=step: self.on_slide(p, v, st))
                sl.pack(side="left", fill="x", expand=True, padx=(0, 10))
                sl.set(val)          # 必须在 pack 之后：画布还没尺寸时 set 会画错位置
                self.vars[path + "#slider"] = sl
            else:
                cell = ctk.CTkFrame(row, fg_color=PAL["panel"], corner_radius=0)
                cell.pack(side="left")
                mk_entry(cell).pack(side="left")
                if fd.get("u"):
                    ctk.CTkLabel(cell, text=fd["u"], font=self.f_small,
                                 text_color=PAL["txt2"]).pack(side="left", padx=(6, 0))
            var.trace_add("write", lambda *a, p=path: self.on_change(p))
            return

        if k == KIND_SEL:
            cur = str(get_path(self.P, path))
            names = [n for _, n in fd["opts"]]
            label_of = {v: n for v, n in fd["opts"]}
            val2key = {n: v for v, n in fd["opts"]}
            row = self._row(box, label)
            var, m = self._option_menu(row, names, label_of.get(cur, names[0]),
                                       lambda val, p=path: self.on_change(p), width=150)
            m.pack(side="left")
            self.vars[path] = ("sel", var, val2key)
            return

        if k == KIND_FONT:
            cur = str(get_path(self.P, path))
            row = self._row(box, label)
            names = list(FONT_NAMES)
            var, m = self._option_menu(row, names, cur if cur in names else DEFAULT_FONT,
                                       lambda val, p=path: self.on_change(p), width=150)
            m.pack(side="left")
            self.vars[path] = ("font", var)
            return

        if k == KIND_SEG:
            row = self._row(box, label)
            self._seg(row, path, fd["opts"], [t for _, t in fd["opts"]])
            self._paint_seg(path, str(get_path(self.P, path)))
            return

        if k == KIND_TEXT:
            row = self._row(box, label)
            var = tk.StringVar(value=str(get_path(self.P, path) or ""))
            self.vars[path] = ("text", var)
            e = ctk.CTkEntry(row, textvariable=var, height=28, corner_radius=7,
                             font=self.f_ui, fg_color=PAL["field"],
                             border_color=PAL["line"], border_width=1,
                             text_color=PAL["txt"])
            e.pack(side="left", fill="x", expand=True)
            var.trace_add("write", lambda *a, p=path: self.on_change(p))
            return

        if k == KIND_COLOR:
            cur = str(get_path(self.P, path))
            var = tk.StringVar(value=cur)
            self.vars[path] = ("color", var)
            row = self._row(box, label)

            def pick(p=path, v=var):
                c = colorchooser.askcolor(color=v.get(), title="选择颜色")[1]
                if c:
                    v.set(c)
                    self.on_change(p)

            sw = ctk.CTkButton(row, text="", width=34, height=24, corner_radius=6,
                               fg_color=cur, hover_color=cur, border_width=1,
                               border_color=PAL["line"], command=pick)
            sw.pack(side="left")
            self.vars[path + "#swatch"] = sw
            for col in PRESET_COLORS:
                b = ctk.CTkButton(row, text="", width=17, height=17, corner_radius=4,
                                  fg_color=col, hover_color=col, border_width=1,
                                  border_color="#ddd9d0",
                                  command=lambda c=col, p=path, v=var: (
                                      v.set(c), self._set_swatch(p, c), self.on_change(p)))
                b.pack(side="left", padx=(6, 0))
            return

        if k == "image":
            row = self._row(box, label)
            self._small_btn(row, "选择 PNG…", self.pick_image, width=96).pack(side="left")
            return

    def _set_swatch(self, path, col):
        sw = self.vars.get(path + "#swatch")
        if sw is not None:
            try:
                sw.configure(fg_color=col, hover_color=col)
            except Exception:
                pass

    # ---------------- 右侧预览
    def _build_stage(self, parent):
        stage = ctk.CTkFrame(parent, fg_color=PAL["bg"], corner_radius=0)
        stage.pack(side="left", fill="both", expand=True)
        self.stage = stage
        self.canvas = tk.Canvas(stage, bg=PAL["bg"], highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True, padx=24, pady=20)
        self.canvas.bind("<Configure>", lambda e: self.schedule())

    def _build_status(self):
        bar = ctk.CTkFrame(self.root, fg_color=PAL["panel"], corner_radius=0, height=30)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        tk.Frame(bar, bg=PAL["line"], height=1).pack(side="top", fill="x")
        self.status = ctk.CTkLabel(bar, text="就绪", font=self.f_small,
                                   text_color=PAL["txt2"], anchor="w")
        self.status.pack(side="left", padx=20, pady=5)
        ctk.CTkLabel(bar, text="内部单位为 mm，导出时按 DPI 换算为像素", font=self.f_small,
                     text_color="#9a978e", anchor="e").pack(side="right", padx=20)

    # ---------------- 交互
    def _fmt(self, v, step):
        try:
            v = float(v)
        except Exception:
            v = 0.0
        try:
            step = float(step) or 1.0
        except Exception:
            step = 1.0
        if step >= 1:
            return str(int(round(v)))
        dec = max(0, min(3, int(math.ceil(-math.log10(step)))))
        return ("%.*f" % (dec, v)).rstrip("0").rstrip(".")

    def on_slide(self, path, v, step=1):
        if self._loading:
            return
        try:
            raw = float(v)
        except Exception:
            return
        try:
            step = float(step) or 1.0
        except Exception:
            step = 1.0
        val = round(round(raw / step) * step, 6)
        if path in ("frame.w", "frame.h"):
            self._set_frame_size("w" if path.endswith("w") else "h", val)
        else:
            set_path(self.P, path, val)
        fdv = self.vars.get(path)
        if fdv and fdv[0] == "num":
            was = self._loading
            self._loading = True
            try:
                fdv[1].set(self._fmt(val, fdv[2].get("step", 1)))
            finally:
                self._loading = was
        self.schedule()

    def on_seg(self, path, value):
        set_path(self.P, path, value)
        self._paint_seg(path, value)
        self.schedule()

    def _paint_seg(self, path, cur):
        btns = self.vars[path][1]
        for v, b in btns.items():
            on = (str(v) == str(cur))
            b.configure(fg_color=PAL["accent"] if on else PAL["field"],
                        hover_color=PAL["accent2"] if on else "#efece6",
                        text_color="#ffffff" if on else PAL["txt2"])

    def on_change(self, path):
        if self._loading:
            return
        info = self.vars.get(path)
        if not info:
            return
        kind = info[0]
        try:
            if kind == "num":
                raw = info[1].get().strip()
                if raw in ("", "-", ".", "-."):
                    return
                val = float(raw)
                fd = info[2]
                val = max(fd["min"], min(fd["max"], val))
                if path in ("frame.w", "frame.h"):
                    self._set_frame_size("w" if path.endswith("w") else "h", val)
                else:
                    set_path(self.P, path, val)
                sl = self.vars.get(path + "#slider")
                if sl is not None:
                    sl.set(val)
            elif kind == "bool":
                set_path(self.P, path, bool(info[1].get()))
            elif kind == "sel":
                set_path(self.P, path, info[2][info[1].get()])
            elif kind in ("font", "text", "color"):
                set_path(self.P, path, info[1].get())
            elif kind == "tex":
                ids, names = info[2], info[3]
                nm = info[1].get()
                set_path(self.P, path, ids[names.index(nm)] if nm in names else "")
        except Exception:
            return
        if kind == "color":
            self._set_swatch(path, info[1].get())
        if path == "frame.shape":
            self._sync_shape_ui()
        self.schedule()

    def schedule(self):
        """节流重绘：连续调参时每 45ms 出一帧。

        原来用「取消 + 70ms 防抖」，拖动滑块期间每一帧都被取消，
        整个拖动过程预览完全不更新，只有停手才出图。
        """
        if self._job:
            return
        self._job = self.root.after(45, self.redraw)

    def redraw(self):
        self._job = None
        box = design_box(self.P)
        cw = max(120, self.canvas.winfo_width() - 8)
        ch = max(120, self.canvas.winfo_height() - 8)
        ppm = min(cw / box["w"], ch / box["h"])
        try:
            img = render_image(self.P, ppm, ss=2, transparent=False, fast=True)
        except Exception as e:
            self.status.configure(text="渲染失败：%s" % e)
            return
        self.photo = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas.create_image(self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2,
                                 image=self.photo, anchor="center")
        dpi = int(self.P["out"]["dpi"])
        px = round(box["w"] / 25.4 * dpi)
        py = round(box["h"] / 25.4 * dpi)
        self.status.configure(
            text="画布 %.1f × %.1f mm　·　导出 %d × %d px @ %d DPI　·　预览 %d px/mm"
                 % (box["w"], box["h"], px, py, dpi, round(ppm)))

    # ---------------- 文件
    ARC_PRESETS = {
        "top":    (0.0, False),
        "bottom": (180.0, True),
        "left":   (270.0, False),
        "right":  (90.0, False),
    }

    def apply_preset(self, i, key):
        """一键把某段文字改为绕中心排布（弧排）。"""
        if key not in self.ARC_PRESETS:
            return
        ang, inward = self.ARC_PRESETS[key]
        t = self.P["texts"][i]
        t["mode"] = "arc"
        t["startAngle"] = ang
        t["inward"] = inward
        t["arcSpan"] = 0.0
        # 弧排位置由半径+角度决定，清掉平排留下的偏移，否则会叠加跑出画布
        t["dx"] = 0.0
        t["dy"] = 0.0
        t["visible"] = True
        self.refresh_all()
        self.redraw()

    def open_tex_dir(self):
        try:
            os.startfile(TEX_DIR)
        except Exception as e:
            messagebox.showerror("打开失败", str(e))

    def load_texture(self):
        paths = filedialog.askopenfilenames(
            title="载入纹理（PNG，可多选）",
            filetypes=[("PNG 图片", "*.png"),
                       ("所有图片", "*.png *.webp *.jpg *.jpeg")])
        if not paths:
            return
        for pth in paths:
            name = os.path.splitext(os.path.basename(pth))[0]
            TEX_FILES[name] = pth
            _tex_cache.pop(name, None)
        self._refresh_tex_combos()
        self.schedule()
        self.status.configure(text="已载入 %d 个纹理，共 %d 个可用"
                                   % (len(paths), len(TEX_FILES) + len(BUILTIN_TEX)))

    def _refresh_tex_combos(self):
        names = ["（无）"] + [n for _, n in BUILTIN_TEX] + list(TEX_FILES.keys())
        for cb in self.tex_combos:
            cb.configure(values=names)

    def pick_image(self):
        p = filedialog.askopenfilename(title="选择图符图片",
                                       filetypes=[("PNG 图片", "*.png"), ("所有图片", "*.png *.jpg *.jpeg *.bmp *.gif")])
        if p:
            self.P["symbol"]["img"] = p
            self.P["symbol"]["kind"] = "image"
            self._loading = True
            st = self.vars.get("symbol.kind")
            if st:
                self._paint_seg("symbol.kind", "image")
            self._loading = False
            self.schedule()

    def export_png(self):
        dpi = int(self.P["out"]["dpi"])
        path = filedialog.asksaveasfilename(
            title="导出 PNG", defaultextension=".png",
            initialfile="图章_%ddpi.png" % dpi,
            filetypes=[("PNG 图片", "*.png")])
        if not path:
            return
        try:
            img = render_image(self.P, dpi / 25.4, ss=3, transparent=True, fast=False)
            img.save(path, "PNG", dpi=(dpi, dpi))
            self.status.configure(text="已导出：%s（%d×%d px）" % (path, img.width, img.height))
        except Exception as e:
            messagebox.showerror("导出失败", str(e))

    def save_json(self):
        path = filedialog.asksaveasfilename(title="保存参数", defaultextension=".json",
                                            initialfile="图章参数.json",
                                            filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.P, f, ensure_ascii=False, indent=2)
            self.status.configure(text="已保存参数：%s" % path)
        except Exception as e:
            messagebox.showerror("保存失败", str(e))

    def load_json(self):
        path = filedialog.askopenfilename(title="载入参数",
                                          filetypes=[("JSON", "*.json"), ("所有文件", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                obj = json.load(f)
            base = default_params()
            for k, v in obj.items():
                if isinstance(v, dict) and isinstance(base.get(k), dict):
                    base[k].update(v)
                elif k == "texts" and isinstance(v, list):
                    base["texts"] = [dict(default_text(i), **v[i]) for i in range(min(3, len(v)))]
                else:
                    base[k] = v
            self.P = base
            self.refresh_all()
            self.schedule()
            self.status.configure(text="已载入参数：%s" % path)
        except Exception as e:
            messagebox.showerror("载入失败", str(e))

    def reset(self):
        self.P = default_params()
        self.refresh_all()
        self.schedule()

    def _nudge(self, path, fd, sign):
        """数字框上滚轮 / 上下键：按 step 微调（网页版 input[type=number] 的手感）。"""
        step = float(fd.get("step", 1) or 1)
        try:
            v = float(get_path(self.P, path)) + sign * step
        except Exception:
            return "break"
        v = max(float(fd["min"]), min(float(fd["max"]), round(v, 6)))
        if path in ("frame.w", "frame.h"):
            self._set_frame_size("w" if path.endswith("w") else "h", v)
        else:
            set_path(self.P, path, v)
        info = self.vars.get(path)
        if info and info[0] == "num":
            was = self._loading
            self._loading = True
            try:
                info[1].set(self._fmt(v, step))
            finally:
                self._loading = was
        self.schedule()
        return "break"

    def _sync_frame_ctl(self, path):
        """把外框宽/高控件的显示值同步成 P 里的当前值（不触发 on_change）。"""
        info = self.vars.get(path)
        if not info or info[0] != "num":
            return
        step = info[2].get("step", 1)
        val = float(get_path(self.P, path))
        was = self._loading
        self._loading = True
        try:
            info[1].set(self._fmt(val, step))
            sl = self.vars.get(path + "#slider")
            if sl is not None:
                sl.set(val)
        finally:
            self._loading = was

    def _set_frame_size(self, axis, val):
        """改外框尺寸的统一入口（与 Web 版 setFrameSize 对应）。

        · 圆章没有独立高度——拖「高度」等于拖直径，两个控件始终同步
        · 勾了「改外框等比缩放」时，按「新尺寸/旧尺寸」把内容等比缩放；
          连续拖动逐次相乘，最终比例正好等于首尾之比，不会累积漂移
        """
        f = self.P["frame"]
        circle = str(f["shape"]) == "circle"
        use_w = (axis == "w") or circle
        old = float(f["w"] if use_w else f["h"]) or 0.0
        k = (val / old) if old else 1.0
        if use_w:
            f["w"] = val
            if circle:
                f["h"] = val
        else:
            f["h"] = val
        if bool(self.P["design"].get("linkScale", True)):
            scale_content(self.P, k)
            if abs(k - 1.0) > 1e-9:
                # 缩放会连带改掉内框/线宽/字号…，控件显示要跟上，否则框里还是旧数字
                self.refresh_all()
        if circle:
            self._sync_frame_ctl("frame.w")
            self._sync_frame_ctl("frame.h")

    def _sync_shape_ui(self):
        """圆章只有一个尺寸：把「高度」对齐到直径并刷新显示，避免两个框数值打架。"""
        f = self.P["frame"]
        if str(f["shape"]) == "circle":
            if float(f["h"]) != float(f["w"]):
                f["h"] = f["w"]
            self._sync_frame_ctl("frame.w")
            self._sync_frame_ctl("frame.h")

    def refresh_all(self):
        """把 self.P 的值回写到所有控件。"""
        self._loading = True
        try:
            for path, info in list(self.vars.items()):
                if path.endswith("#slider") or path.endswith("#swatch"):
                    continue
                kind = info[0]
                try:
                    val = get_path(self.P, path)
                except Exception:
                    continue
                if kind == "num":
                    info[1].set(self._fmt(val, info[2].get("step", 1)))
                    sl = self.vars.get(path + "#slider")
                    if sl is not None:
                        sl.set(float(val))
                elif kind == "bool":
                    info[1].set(bool(val))
                elif kind == "sel":
                    for v, n in info[2].items():
                        if str(v) == str(val):
                            info[1].set(n)
                elif kind in ("font", "text"):
                    info[1].set(str(val if val is not None else ""))
                elif kind == "color":
                    info[1].set(str(val))
                    self._set_swatch(path, str(val))
                elif kind == "tex":
                    ids, names = info[2], info[3]
                    v = str(val or "")
                    info[1].set(names[ids.index(v)] if v in ids else "（无）")
                elif kind == "seg":
                    self._paint_seg(path, str(val))
        finally:
            self._loading = False
        sync = getattr(self, "_sync_scroll", None)
        if sync:
            try:
                sync()
            except Exception:
                pass
        try:
            self._sync_shape_ui()
        except Exception:
            pass


def main():
    root = ctk.CTk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
