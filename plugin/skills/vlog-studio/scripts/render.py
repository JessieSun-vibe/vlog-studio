#!/usr/bin/env python3
"""按时间线 JSON 渲染成片（MP4 + 双语 SRT）。格式见 references/timeline-format.md。

  uv run --with pillow --with resvg-py python render.py <timeline.json> --style <style.json> [--only 3,4] [--work <目录>]

每个片段单独渲染（画面、角标、章节标签、贴图、花字、字幕、声音），再无损拼接，最后混音效 / 背景音乐并统一响度。
需要 ffmpeg（带 libvpx 解码器才能读带透明的 webm 贴图）。
"""
import argparse, colorsys, json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageOps
for _s in (sys.stdout, sys.stderr):  # 英文版 Windows 的终端不是 UTF-8，打印中文会报错
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline_tools import split_sub  # noqa: E402

FALLBACK_FONTS = ["/System/Library/Fonts/Hiragino Sans GB.ttc", "/System/Library/Fonts/STHeiti Medium.ttc",
                  "/System/Library/Fonts/PingFang.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                  "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/simhei.ttf"]


# ---------------- 风格 ----------------
def load_style(path):
    st = json.load(open(os.path.expanduser(path), encoding="utf-8"))
    def font(key, default=None):
        want = st.get("fonts", {}).get(key)
        for p in [want, default, *FALLBACK_FONTS]:
            if p and os.path.exists(os.path.expanduser(p)):
                if want and p != want:
                    print(f"⚠️ 找不到字体 {want}，{key} 改用 {p}")
                return os.path.expanduser(p)
        raise SystemExit(f"找不到字体：{key}")
    st["_font_sub"] = font("subtitle")
    st["_font_fun"] = font("fun", st["_font_sub"])
    st["_font_brand"] = font("brand", st["_font_fun"])
    return st


def hexrgb(h, a=255):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-3000:]); raise SystemExit("ffmpeg 出错（上面是错误信息）")


# ---------------- 叠加层（PIL 画 PNG）----------------
def outlined(d, xy, text, font, fill, stroke, sw, anchor="mm"):
    d.text(xy, text, font=font, fill=fill, stroke_width=sw, stroke_fill=stroke, anchor=anchor)


def brand_png(st, W, H, text, path):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if text:
        b = st.get("brand", {}); d = ImageDraw.Draw(c)
        outlined(d, (b.get("x", 60), b.get("y", 62)), text, ImageFont.truetype(st["_font_brand"], b.get("size", 58)),
                 hexrgb(b.get("color", "#ffffff")), (0, 0, 0, 90), 4, anchor="lm")
    c.save(path)


def tag_png(st, text, path):
    t = st.get("chapter_tag", {}); f = ImageFont.truetype(st["_font_fun"], t.get("size", 46))
    c = Image.new("RGBA", (900, 100), (0, 0, 0, 0)); d = ImageDraw.Draw(c); x, y = 4, 20
    pin = hexrgb(t.get("pin_color", "#ff4d6d"))
    d.ellipse([x, y - 2, x + 34, y + 32], fill=pin, outline="white", width=4)
    d.polygon([(x + 6, y + 26), (x + 28, y + 26), (x + 17, y + 50)], fill=pin)
    d.ellipse([x + 11, y + 9, x + 23, y + 21], fill="white")
    outlined(d, (x + 50, y + 18), text, f, hexrgb(t.get("color", "#ff5c8a")), "white", 6, anchor="lm")
    c.crop(c.getbbox()).save(path)


def fx_png(st, text, path):
    fx = st.get("fx", {}); f = ImageFont.truetype(st["_font_fun"], fx.get("size", 118))
    c = Image.new("RGBA", (1800, 340), (0, 0, 0, 0)); d = ImageDraw.Draw(c); sw = fx.get("stroke_width", 12)
    d.text((906, 178), text, font=f, fill=(0, 0, 0, 90), stroke_width=sw + 2, stroke_fill=(0, 0, 0, 90), anchor="mm")
    outlined(d, (900, 170), text, f, hexrgb(fx.get("fill", "#ffd640")), hexrgb(fx.get("stroke", "#ff6a2c")), sw)
    c = c.rotate(fx.get("rotate", 4), resample=Image.BICUBIC); c.crop(c.getbbox()).save(path)


def sub_png(st, W, H, cn, en, path):
    s = st.get("subtitles", {}); c = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    fc = ImageFont.truetype(st["_font_sub"], s.get("cn_size", 51)); fe = ImageFont.truetype(st["_font_sub"], s.get("en_size", 33))
    first, second = (cn, en) if s.get("order", "cn_en") == "cn_en" else (en, cn)
    f1, f2 = (fc, fe) if first == cn else (fe, fc)
    y = s.get("y", int(H * .85)); gap = s.get("line_gap", 56)
    bw = max(d.textlength(first, font=f1), d.textlength(second, font=f2) if second else 0) + 60
    hgt = (gap + 60) if second else 66
    box = Image.new("RGBA", c.size, (0, 0, 0, 0))
    ImageDraw.Draw(box).rounded_rectangle([(W - bw) / 2, y - 12, (W + bw) / 2, y + hgt], 18, fill=(0, 0, 0, s.get("box_alpha", 115)))
    c.alpha_composite(box); d = ImageDraw.Draw(c)
    d.text((W / 2, y + 30), first, font=f1, fill="white", anchor="mm")
    if second:
        d.text((W / 2, y + 30 + gap), second, font=f2, fill=(235, 235, 235), anchor="mm")
    c.save(path)


def cover(img, w, h, cx=.5, cy=.5):
    s = max(w / img.width, h / img.height)
    im = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    x = int((im.width - w) * cx); y = int((im.height - h) * cy)
    return im.crop((x, y, x + w, y + h))


def pop_expr(a):
    """花字 / 静态贴图的弹出：0 → 1.15 → 1。"""
    return (f"if(lt(t,{a:.3f}),0.02,if(lt(t,{a + .18:.3f}),0.3+0.85*(t-{a:.3f})/0.18,"
            f"if(lt(t,{a + .3:.3f}),1.15-0.15*(t-{a + .18:.3f})/0.12,1)))")


# ---------------- 跟着脸走的贴图 / 信息卡 ----------------
def face_positions(track_path, who, times):
    """按时间取第 who 个人（从左往右数）的脸：返回 [(cx, cy, w)]（0–1 比例），中间线性插值。
    用全片中位位置给每个人定「角色」，某一帧少检测到一张脸时按最近距离匹配，不会把人认错。"""
    import statistics
    tr = json.load(open(track_path, encoding="utf-8")); S = tr["samples"]
    n = max(len(x["faces"]) for x in S)
    full = [x["faces"] for x in S if len(x["faces"]) == n]
    roles = [statistics.median(f[i]["cx"] for f in full) for i in range(n)]
    pts = []
    for x in S:
        if not x["faces"]:
            continue
        f = min(x["faces"], key=lambda q: abs(q["cx"] - roles[who]))
        if abs(f["cx"] - roles[who]) < .12:
            pts.append((x["t"], f["cx"], f["cy"], f["w"]))
    out = []
    for t in times:
        if t <= pts[0][0]:
            out.append(pts[0][1:]); continue
        if t >= pts[-1][0]:
            out.append(pts[-1][1:]); continue
        k = next(i for i in range(1, len(pts)) if pts[i][0] >= t); a, b = pts[k - 1], pts[k]
        r = (t - a[0]) / max(1e-6, b[0] - a[0])
        out.append(tuple(a[j] + (b[j] - a[j]) * r for j in (1, 2, 3)))
    return out


def follow_layer(sticker, p, dur, W, H, FPS, d, q):
    """把贴图（webm 动图 / png / svg）画成一段跟着脸走的透明视频（qtrle .mov），返回路径。"""
    import math, shutil
    f = sticker["follow"]; path = os.path.expanduser(sticker["file"])
    fdir = os.path.join(d, f"follow{q}"); os.makedirs(fdir, exist_ok=True)
    if path.endswith(".webm"):
        run(["ffmpeg", "-v", "error", "-y", "-c:v", "libvpx", "-i", path, "-vf", f"fps={FPS}", "-pix_fmt", "rgba", os.path.join(fdir, "s%04d.png")])
        frames = [Image.open(os.path.join(fdir, x)).convert("RGBA") for x in sorted(os.listdir(fdir)) if x.startswith("s")]
    else:
        if path.endswith(".svg"):
            import resvg_py
            png = os.path.join(fdir, "s.png"); open(png, "wb").write(bytes(resvg_py.svg_to_bytes(svg_path=path, width=512))); path = png
        frames = [Image.open(path).convert("RGBA")]
    v = p["video"]; sp = v.get("speed", 1.0); at = sticker.get("at", 0.0); until = sticker.get("until", dur)
    n = int(round(dur * FPS))
    times = [v.get("start", 0) + (k / FPS) * sp for k in range(n)]
    pos = face_positions(f["track"], f.get("who", 0), times)
    tr = json.load(open(f["track"], encoding="utf-8")); sx, sy = W, H  # 轨迹是 0–1 比例，按输出画面换算（源画面同比例）
    out = os.path.join(d, f"follow{q}.mov")
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
                             "-i", "-", "-c:v", "qtrle", out], stdin=subprocess.PIPE)
    blank = Image.new("RGBA", (W, H), (0, 0, 0, 0)).tobytes()
    for k in range(n):
        t = k / FPS
        if t < at or t > until:
            proc.stdin.write(blank); continue
        cx, cy, fw = pos[k]
        size = max(24, int(fw * sx * f.get("size", .7)))
        im = frames[int((t - at) * FPS) % len(frames)] if f.get("loop", True) else frames[min(len(frames) - 1, int((t - at) * FPS))]
        im = im.resize((size, size), Image.LANCZOS)
        pop = min(1.0, (t - at) / .25) if (t - at < .25 and f.get("pop", True)) else 1.0   # 跨剪辑点延续的贴图设 pop:false
        if pop < 1:
            s2 = max(4, int(size * (0.3 + 0.85 * pop))); im = im.resize((s2, s2), Image.LANCZOS)
        bob = math.sin((t - at) * 2 * math.pi * f.get("bob_hz", .8)) * fw * sx * .04
        x = int(cx * sx + f.get("dx", .8) * fw * sx - im.width / 2)
        y = int(cy * sy + f.get("dy", -.6) * fw * sx - im.height / 2 + bob)
        c = Image.new("RGBA", (W, H), (0, 0, 0, 0)); c.alpha_composite(im, (min(max(0, x), W - im.width), min(max(0, y), H - im.height)))
        proc.stdin.write(c.tobytes())
    proc.stdin.close(); proc.wait()
    shutil.rmtree(fdir, ignore_errors=True)
    return out


def card_png(st, card, path):
    """信息卡：白色纸片 + 大字（站酷快乐体）+ 英文小字 + 一排小图标，略微倾斜。"""
    ft = ImageFont.truetype(st["_font_fun"], card.get("title_size", 86)); fs = ImageFont.truetype(st["_font_sub"], card.get("sub_size", 34))
    d0 = ImageDraw.Draw(Image.new("L", (1, 1)))
    tw = d0.textlength(card["title"], font=ft); sw_ = d0.textlength(card.get("sub", ""), font=fs)
    icons = []
    for ic in card.get("icons", []):
        ic = os.path.expanduser(ic)
        if not os.path.exists(ic):
            continue
        if ic.endswith(".svg"):
            import resvg_py, io
            icons.append(Image.open(io.BytesIO(bytes(resvg_py.svg_to_bytes(svg_path=ic, width=160)))).convert("RGBA"))
        else:
            icons.append(Image.open(ic).convert("RGBA").resize((160, 160)))
    isz = 84; w = int(max(tw, sw_, len(icons) * (isz + 14)) + 120); h = 120 + 96 + (60 if card.get("sub") else 0) + (isz + 20 if icons else 0)
    c = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rounded_rectangle([26, 30, w + 26, h + 30], 28, fill=(0, 0, 0, 60))
    d.rounded_rectangle([20, 20, w + 20, h + 20], 28, fill=hexrgb(card.get("bg", "#fffaf3")))
    y = 70
    if icons:
        x0 = 20 + (w - len(icons) * (isz + 14) + 14) // 2
        for k, im in enumerate(icons):
            c.alpha_composite(im.resize((isz, isz), Image.LANCZOS), (x0 + k * (isz + 14), y - 20))
        y += isz + 10
    d.text((20 + w / 2, y + 40), card["title"], font=ft, fill=hexrgb(card.get("color", "#ff5c8a")), anchor="mm")
    if card.get("sub"):
        d.text((20 + w / 2, y + 112), card["sub"], font=fs, fill=hexrgb(card.get("sub_color", "#6b5b4e")), anchor="mm")
    c = c.rotate(card.get("rotate", -3), expand=True, resample=Image.BICUBIC); c.crop(c.getbbox()).save(path)


# ---------------- 单个片段 ----------------
def piece_duration(p):
    au = p.get("audio", {"type": "none"})
    if au.get("type") == "vo":
        return au["to"] - au["from"]
    return p["duration"]


def render_piece(i, p, tl, st, work, first_in_chapter):
    W, H = tl.get("size", [1920, 1080]); FPS = tl.get("fps", 30)
    d = os.path.join(work, f"p{i + 1:02d}"); os.makedirs(d, exist_ok=True)
    dur = piece_duration(p); ins, fc = [], []
    k = lambda: sum(1 for x in ins if x == "-i")
    v = p["video"]; vid_k = None
    # 画面
    if "montage" in v:
        n = len(v["montage"]); each = dur / n; labs = []
        for m, (src, t) in enumerate(v["montage"]):
            j = k(); ins += ["-ss", f"{t}", "-t", f"{each + .1:.3f}", "-i", src]
            fc.append(f"[{j}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},setsar=1,trim=duration={each:.3f},setpts=PTS-STARTPTS[m{m}]")
            labs.append(f"[m{m}]")
        fc.append(f"{''.join(labs)}concat=n={n}:v=1:a=0,tpad=stop_mode=clone:stop_duration=1,trim=duration={dur:.3f}[bg]")
    elif "photo" in v:
        im = ImageOps.exif_transpose(Image.open(v["photo"])).convert("RGB")
        still = os.path.join(d, "still.png"); cover(im, W * 2, H * 2, v.get("cx", .5), v.get("cy", .5)).save(still)
        j = k(); ins += ["-loop", "1", "-t", f"{dur:.3f}", "-i", still]
        z = v.get("zoom", .10)
        fc.append(f"[{j}:v]zoompan=z='1+{z}*on/({dur:.3f}*{FPS})':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s={W}x{H}:fps={FPS},setsar=1[bg]")
    else:
        sp = v.get("speed", 1.0); vid_k = k()
        ins += ["-ss", f"{v['start']:.3f}", "-t", f"{dur * sp + .05:.3f}", "-i", v["src"]]
        fc.append(f"[{vid_k}:v]setpts=PTS/{sp},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                  f"fps={FPS},setsar=1,tpad=stop_mode=clone:stop_duration=2,trim=duration={dur:.3f}[bg]")
    # 声音
    au = p.get("audio", {"type": "none"}); typ = au.get("type", "none")
    norm = f"loudnorm=I={st.get('speech_lufs', -17)}:TP=-2:LRA=9"
    sp = v.get("speed", 1.0)
    clip_a = (f"[{vid_k}:a:0]aresample=48000,aformat=channel_layouts=stereo,atempo={max(sp, .5)}" if vid_k is not None else None)
    if typ == "vo":
        j = k(); ins += ["-ss", f"{au['from']:.3f}", "-t", f"{dur:.3f}", "-i", tl["voiceover"]]
        fc.append(f"[{j}:a]aresample=48000,aformat=channel_layouts=stereo,afade=t=in:d=0.015,"
                  f"afade=t=out:st={dur - .02:.3f}:d=0.02,{norm},apad,atrim=duration={dur:.3f}[voa]")
        if clip_a:
            fc.append(f"{clip_a},volume={p.get('bg_volume', st.get('bg_under_speech', .12))},apad,atrim=duration={dur:.3f}[bga]")
            fc.append("[voa][bga]amix=inputs=2:normalize=0:duration=first[a]")
        else:
            fc.append("[voa]anull[a]")
    elif typ == "clip" and clip_a:
        fc.append(f"{clip_a},highpass=f=90,{norm},apad,atrim=duration={dur:.3f}[a]")
    elif typ == "music" and clip_a:
        fc.append(f"{clip_a},loudnorm=I={st.get('music_lufs', -19)}:TP=-2,apad,atrim=duration={dur:.3f}[a]")
    elif typ == "ambient" and clip_a:
        fc.append(f"{clip_a},volume={p.get('bg_volume', .5)},apad,atrim=duration={dur:.3f}[a]")
    else:
        j = k(); ins += ["-f", "lavfi", "-t", f"{dur:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
        fc.append(f"[{j}:a]anull[a]")
    # 叠加层
    cur = "bg"

    def img(path):
        j = k(); ins.extend(["-loop", "1", "-t", f"{dur:.3f}", "-i", path]); return j

    brand_png(st, W, H, tl.get("brand", st.get("brand", {}).get("text", "")), os.path.join(d, "brand.png"))
    j = img(os.path.join(d, "brand.png")); fc.append(f"[{cur}][{j}:v]overlay=0:0[v_b]"); cur = "v_b"
    if p.get("tag"):
        tg = st.get("chapter_tag", {}); tag_png(st, p["tag"], os.path.join(d, "tag.png")); j = img(os.path.join(d, "tag.png"))
        x0 = tg.get("x", 62); x = f"{x0}-500*pow(max(0,1-t/0.35),2)" if first_in_chapter else f"{x0}"
        fc.append(f"[{cur}][{j}:v]overlay=x='{x}':y={tg.get('y', 118)}:eval=frame[v_t]"); cur = "v_t"
    if v.get("pip"):
        pip = ImageOps.exif_transpose(Image.open(v["pip"])).convert("RGB")
        pip = ImageOps.expand(cover(pip, 300, 400), border=12, fill="white").convert("RGBA").rotate(-5, expand=True, resample=Image.BICUBIC)
        pip.save(os.path.join(d, "pip.png")); j = img(os.path.join(d, "pip.png"))
        fc.append(f"[{cur}][{j}:v]overlay=x={W - pip.width - 70}:y=90[v_p]"); cur = "v_p"
    for q, s in enumerate(p.get("stickers", [])):
        path, size, at = os.path.expanduser(s["file"]), s.get("size", 220), s.get("at", .3)
        if not os.path.exists(path):
            print(f"  ⚠️ 片段 {i + 1}：找不到贴图 {path}，跳过", flush=True); continue
        if path.endswith(".svg"):
            import resvg_py
            png = os.path.join(d, f"stk{q}.png"); open(png, "wb").write(bytes(resvg_py.svg_to_bytes(svg_path=path, width=512))); path = png
        if s.get("follow"):
            mov = follow_layer(s, p, dur, W, H, FPS, d, q); j = k(); ins.extend(["-i", mov])
            fc.append(f"[{cur}][{j}:v]overlay=0:0:eof_action=pass[v_s{q}]"); cur = f"v_s{q}"; continue
        if path.endswith(".webm"):
            j = k(); ins.extend(["-c:v", "libvpx", "-i", path])
            fc.append(f"[{j}:v]format=rgba,fps={FPS},scale={size}:{size},setpts=PTS-STARTPTS+{at:.3f}/TB[st{q}]")
            fc.append(f"[{cur}][st{q}]overlay=x={s['x'] - size // 2}:y={s['y'] - size // 2}:eof_action=pass[v_s{q}]")
        else:
            j = img(path)
            fc.append(f"[{j}:v]format=rgba,scale={size}:-2,scale=w='trunc(iw*{pop_expr(at)}/2)*2':h=-2:eval=frame[st{q}]")
            fc.append(f"[{cur}][st{q}]overlay=x='{s['x']}-overlay_w/2':y='{s['y']}-overlay_h/2':enable='gte(t,{at:.3f})':eval=frame[v_s{q}]")
        cur = f"v_s{q}"
    if p.get("fx"):
        at = p["fx"].get("at", .25); fx_png(st, p["fx"]["text"], os.path.join(d, "fx.png")); j = img(os.path.join(d, "fx.png"))
        y = p["fx"].get("y", st.get("fx", {}).get("y", int(H * .27)))   # 单个镜头可以改高度，避开人脸
        fc.append(f"[{j}:v]format=rgba,scale=w='trunc(iw*{pop_expr(at)}/2)*2':h=-2:eval=frame[fx]")
        fc.append(f"[{cur}][fx]overlay=x='{W // 2}-overlay_w/2':y='{y}-overlay_h/2':enable='gte(t,{at:.3f})':eval=frame[v_f]"); cur = "v_f"
    if p.get("card"):
        cd = p["card"]; at = cd.get("at", .3); card_png(st, cd, os.path.join(d, "card.png")); j = img(os.path.join(d, "card.png"))
        y = cd.get("y", int(H * .62))
        fc.append(f"[{j}:v]format=rgba,scale=w='trunc(iw*{pop_expr(at)}/2)*2':h=-2:eval=frame[cd]")
        fc.append(f"[{cur}][cd]overlay=x='{cd.get('x', W // 2)}-overlay_w/2':y='{y}-overlay_h/2':enable='gte(t,{at:.3f})':eval=frame[v_c]"); cur = "v_c"
    srt = []
    fsub = ImageFont.truetype(st["_font_sub"], st.get("subtitles", {}).get("cn_size", 51))
    meas = lambda t: ImageDraw.Draw(Image.new("L", (1, 1))).textlength(t, font=fsub)
    m = 0
    for t0, t1, cn, en in p.get("subs", []):
        t0, t1 = max(0.0, t0), min(t1, dur)          # 字幕不越过片段边界，避免和下一段重叠
        if t1 - t0 < .05:
            continue
        parts = split_sub(cn, en, meas, st.get("subtitles", {}).get("max_width", 1400))
        total = sum(len(x[0]) for x in parts); a = t0
        for n_, (c1, e1) in enumerate(parts):
            b = t1 if n_ == len(parts) - 1 else a + (t1 - t0) * len(c1) / total
            sub_png(st, W, H, c1, e1, os.path.join(d, f"sub{m}.png")); j = img(os.path.join(d, f"sub{m}.png"))
            fc.append(f"[{cur}][{j}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[v_u{m}]"); cur = f"v_u{m}"
            srt.append((a, b, c1, e1)); a = b; m += 1
    fc.append(f"[{cur}]format=yuv420p[vo]")
    out = os.path.join(d, "seg.mp4")
    run(["ffmpeg", "-y", *ins, "-filter_complex", ";".join(fc), "-map", "[vo]", "-map", "[a]", "-t", f"{dur:.3f}",
         "-r", f"{FPS}", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", out])
    return out, dur, srt


def srt_time(t):
    ms = int(round(t * 1000)); return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def make_pop(path):
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", "aevalsrc='0.55*sin(2*PI*(1400-9000*t)*t)*exp(-38*t)':s=48000:d=0.14", "-ac", "2", path])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("timeline"); ap.add_argument("--style", default="~/.claude/vlog-studio/style.json")
    ap.add_argument("--work"); ap.add_argument("--only", help="只重渲这些片段号，如 3,4（其余用上次的结果）")
    a = ap.parse_args()
    tl = json.load(open(a.timeline, encoding="utf-8")); st = load_style(a.style)
    out = tl["output"]; work = a.work or os.path.splitext(out)[0] + "_work"; os.makedirs(work, exist_ok=True)
    only = {int(x) for x in a.only.split(",")} if a.only else None
    pop = os.path.join(work, "pop.wav"); make_pop(pop)
    sfx_files = {k: os.path.expanduser(v) for k, v in st.get("sfx", {}).items() if v}
    sfx_files.setdefault("pop", pop)
    segs, ev, srt, t, prev = [], [], [], 0.0, None
    for i, p in enumerate(tl["pieces"]):
        first = p.get("chapter") != prev
        seg_path = os.path.join(work, f"p{i + 1:02d}", "seg.mp4")
        if only is None or (i + 1) in only or not os.path.exists(seg_path):
            print(f"片段 {i + 1}/{len(tl['pieces'])}", flush=True)
            seg_path, dur, s_srt = render_piece(i, p, tl, st, work, first)
            json.dump(s_srt, open(seg_path + ".srt.json", "w", encoding="utf-8"), ensure_ascii=False)
        else:
            dur = piece_duration(p); s_srt = json.load(open(seg_path + ".srt.json", encoding="utf-8"))
        segs.append(seg_path)
        for e in p.get("sfx", []):
            f = sfx_files.get(e.get("name"), os.path.expanduser(e.get("file", "")))
            if f and os.path.exists(f):
                ev.append((t + e.get("at", .03), f, e.get("gain", .7)))
            else:
                print(f"  ⚠️ 片段 {i + 1}：找不到音效 {e.get('name') or e.get('file')}（{f or '风格档案里没配'}），跳过")
        if p.get("fx"):
            ev.append((t + p["fx"].get("at", .25), sfx_files["pop"], .8))
        srt += [(t + x0, t + x1, cn, en) for x0, x1, cn, en in s_srt]
        prev = p.get("chapter"); t += dur
    lst = os.path.join(work, "list.txt")
    open(lst, "w", encoding="utf-8").writelines(f"file '{s}'\n" for s in segs)
    joined = os.path.join(work, "joined.mp4")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined])
    ins, fc, labels = ["-i", joined], [], ["[0:a]"]
    for m, (et, path, g) in enumerate(ev):
        ins += ["-i", path]; ms = int(et * 1000)
        fc.append(f"[{m + 1}:a]aresample=48000,aformat=channel_layouts=stereo,volume={g},adelay={ms}|{ms}[x{m}]"); labels.append(f"[x{m}]")
    mix = f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0:duration=first[mx]"
    fc.append(mix)
    if tl.get("bgm"):
        b = tl["bgm"]; j = len(labels)
        ins += ["-stream_loop", "-1", "-i", b["file"]]
        fc.append(f"[{j}:a]aresample=48000,aformat=channel_layouts=stereo,volume={b.get('volume', .15)},atrim=duration={t:.3f}[bgm0]")
        fc.append("[mx]asplit=2[mx1][key]")
        fc.append("[bgm0][key]sidechaincompress=threshold=0.03:ratio=6:attack=30:release=500[bgm1]")
        fc.append("[mx1][bgm1]amix=inputs=2:normalize=0:duration=first[mx2]"); last = "mx2"
    else:
        last = "mx"
    fc.append(f"[{last}]afade=t=out:st={max(0, t - 1.2):.2f}:d=1.2,loudnorm=I={st.get('master_lufs', -16)}:TP=-1.5[ao]")
    run(["ffmpeg", "-y", *ins, "-filter_complex", ";".join(fc), "-map", "0:v", "-map", "[ao]", "-c:v", "copy",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", out])
    merged = []                                   # 一句话跨了剪辑点时，SRT 里合成一条
    for x in srt:
        if merged and merged[-1][2] == x[2] and merged[-1][3] == x[3] and x[0] - merged[-1][1] < .05:
            merged[-1] = (merged[-1][0], x[1], x[2], x[3])
        else:
            merged.append(x)
    srt = merged
    with open(os.path.splitext(out)[0] + ".srt", "w", encoding="utf-8") as f:
        for n, (x0, x1, cn, en) in enumerate(srt, 1):
            f.write(f"{n}\n{srt_time(x0)} --> {srt_time(x1)}\n{cn}\n" + (f"{en}\n" if en else "") + "\n")
    print(f"完成：{out}（{t:.1f}s，{len(srt)} 条字幕，{len(ev)} 个音效）")


if __name__ == "__main__":
    main()
