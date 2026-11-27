#!/usr/bin/env python3
"""分镜：渲染成片之前给用户确认用。

  uv run --with pillow --with resvg-py python storyboard.py <timeline.json> --out <目录> [--style <style.json>] [--speed 1.2]

每个片段出一张「关键时刻」样张：真实画面 + 角标 + 章节标签 + 花字 + 信息卡 + 贴图（含跟着脸走的贴图）+ 当时的字幕，
全部画在成片里的真实位置上（贴图压脸、信息卡挡人这类问题在这里就能看出来）。
同时输出：
  <目录>/storyboard.html  图文分镜页（图片内嵌，可直接发给用户或发布）
  <目录>/storyboard.md    文字版分镜表（贴在对话里）
时间同时给出原速和变速后（--speed，默认读风格档案 default_speed）的成片时间码。
"""
import argparse, base64, html, json, os, subprocess, sys
from PIL import Image, ImageOps
for _s in (sys.stdout, sys.stderr):  # 英文版 Windows 的终端不是 UTF-8，打印中文会报错
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from render import (load_style, brand_png, tag_png, fx_png, sub_png, card_png, cover, piece_duration,  # noqa: E402
                    face_positions)


def at_of(x, default=0.0):
    return x.get("at", default) if isinstance(x, dict) else default


def key_moment(p, dur):
    """片段里最「满」的那一刻：所有元素都已经出现之后一点点。"""
    ts = [at_of(s, .3) for s in p.get("stickers", [])] + ([p["fx"].get("at", .25)] if p.get("fx") else []) \
         + ([p["card"].get("at", .3)] if p.get("card") else [])
    t = (max(ts) + .5) if ts else dur / 2
    return min(max(0.0, t), max(0.0, dur - .1))


def source_time(p, t):
    v = p["video"]
    if "montage" in v:
        n = len(v["montage"]); k = min(n - 1, int(t / (piece_duration(p) / n))); src, s0 = v["montage"][k]
        return src, s0 + t - k * piece_duration(p) / n
    if "photo" in v:
        return v["photo"], 0.0
    return v["src"], v.get("start", 0) + t * v.get("speed", 1.0)


def grab(src, t, path, W, H, v):
    if src.lower().endswith((".jpg", ".jpeg", ".png", ".heic")):
        im = ImageOps.exif_transpose(Image.open(src)).convert("RGB"); return cover(im, W, H, v.get("cx", .5), v.get("cy", .5))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", src, "-frames:v", "1", path], check=True)
    return cover(Image.open(path).convert("RGB"), W, H)


def sticker_image(path, tmpdir):
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        return None
    if path.endswith(".svg"):
        import io, resvg_py
        return Image.open(io.BytesIO(bytes(resvg_py.svg_to_bytes(svg_path=path, width=512)))).convert("RGBA")
    if path.endswith(".webm"):
        out = os.path.join(tmpdir, os.path.basename(path) + ".png")
        if not os.path.exists(out):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-c:v", "libvpx", "-ss", "0.6", "-i", path, "-frames:v", "1",
                            "-pix_fmt", "rgba", out], check=True)
        return Image.open(out).convert("RGBA")
    return Image.open(path).convert("RGBA")


CATALOG = {}


def load_catalog(st):
    """素材清单里的中文名（「revolving-hearts」→「旋转爱心」），分镜里给人看。"""
    path = os.path.expanduser(st.get("asset_catalog", "") or "")
    if os.path.exists(path):
        for it in json.load(open(path, encoding="utf-8")):
            CATALOG[it["name"]] = it.get("meaning", "").split("｜")[0] or it["name"]


def describe_sticker(s, W=1920, n_faces=2):
    name = os.path.splitext(os.path.basename(s["file"]))[0]; zh = CATALOG.get(name, name)
    if s.get("follow"):
        f = s["follow"]; side = "右" if f.get("dx", .8) > 0 else "左"; who = f.get("who", 0)
        person = ("左边的人" if who == 0 else "右边的人") if n_faces == 2 else f"从左数第 {who + 1} 个人"
        return f"{zh}（跟着{person}的脸，在脸{side}上方，{at_of(s, 0):.1f}s 出现）"
    x = s.get("x", W / 2); area = "画面左侧" if x < W / 3 else ("画面右侧" if x > W * 2 / 3 else "画面中间")
    return f"{zh}（{at_of(s, .3):.1f}s，{area}）"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("timeline"); ap.add_argument("--style", default="~/.claude/vlog-studio/style.json")
    ap.add_argument("--out", required=True); ap.add_argument("--speed", type=float)
    a = ap.parse_args()
    tl = json.load(open(a.timeline, encoding="utf-8")); st = load_style(a.style); W, H = tl.get("size", [1920, 1080]); load_catalog(st)
    speed = a.speed or st.get("default_speed", 1.0)
    sd = os.path.join(a.out, "stills"); os.makedirs(sd, exist_ok=True)
    rows, md, t = [], [], 0.0
    md.append(f"| # | 成片时间（{speed:g} 倍速后） | 声音 / 原片 | 字幕 | 花字 · 信息卡 | 贴图 | 音效 |")
    md.append("|---|---|---|---|---|---|---|")
    for i, p in enumerate(tl["pieces"]):
        n = i + 1; dur = piece_duration(p); km = key_moment(p, dur)
        src, ts = source_time(p, km)
        c = grab(src, ts, os.path.join(sd, f"raw{n:02d}.png"), W, H, p["video"]).convert("RGBA")
        tmp = os.path.join(sd, "tmp.png")
        brand_png(st, W, H, tl.get("brand", st.get("brand", {}).get("text", "")), tmp); c.alpha_composite(Image.open(tmp))
        if p.get("tag"):
            tag_png(st, p["tag"], tmp); tg = st.get("chapter_tag", {}); c.alpha_composite(Image.open(tmp), (tg.get("x", 62), tg.get("y", 118)))
        for s in p.get("stickers", []):
            if at_of(s, .3) > km or (s.get("until") is not None and s["until"] < km):
                continue
            im = sticker_image(s["file"], sd)
            if im is None:
                continue
            if s.get("follow"):
                f = s["follow"]; cx, cy, fw = face_positions(f["track"], f.get("who", 0), [ts])[0]
                size = max(24, int(fw * W * f.get("size", .7))); im = im.resize((size, size))
                x = int(cx * W + f.get("dx", .8) * fw * W - size / 2); y = int(cy * H + f.get("dy", -.6) * fw * W - size / 2)
            else:
                size = s.get("size", 220); im = im.resize((size, int(size * im.height / im.width)))
                x, y = int(s["x"] - im.width / 2), int(s["y"] - im.height / 2)
            c.alpha_composite(im, (min(max(0, x), W - im.width), min(max(0, y), H - im.height)))
        if p.get("fx") and p["fx"].get("at", .25) <= km:
            fx_png(st, p["fx"]["text"], tmp); im = Image.open(tmp); y = p["fx"].get("y", st.get("fx", {}).get("y", int(H * .27)))
            c.alpha_composite(im, ((W - im.width) // 2, y - im.height // 2))
        if p.get("card") and p["card"].get("at", .3) <= km:
            cd = p["card"]; card_png(st, cd, tmp); im = Image.open(tmp)
            c.alpha_composite(im, (int(cd.get("x", W // 2) - im.width / 2), int(cd.get("y", H * .62) - im.height / 2)))
        cur = [s for s in p.get("subs", []) if s[0] <= km <= s[1]] or p.get("subs", [])[:1]
        if cur:
            sub_png(st, W, H, cur[0][2], cur[0][3], tmp); c.alpha_composite(Image.open(tmp))
        still = os.path.join(sd, f"s{n:02d}.jpg"); c.convert("RGB").resize((800, 450)).save(still, quality=84)
        b64 = base64.b64encode(open(still, "rb").read()).decode()
        au = p.get("audio", {"type": "none"}); typ = au.get("type", "none")
        if typ == "vo":
            snd = f"口播 {au['from']:.2f}–{au['to']:.2f}s"
        elif typ == "clip":
            v = p["video"]; snd = f"原声 原片 {v.get('start', 0):.2f}–{v.get('start', 0) + dur * v.get('speed', 1):.2f}s"
        else:
            snd = {"music": "现场音乐", "ambient": "环境声", "none": "无声"}.get(typ, typ)
        vid = os.path.basename(p["video"].get("src") or p["video"].get("photo") or "快剪")
        subs_h = "<br>".join(f"<span class=tc>{x[0]:.1f}s</span> {html.escape(x[2])}<br><span class=en>{html.escape(x[3])}</span>" for x in p.get("subs", []))
        subs_m = " / ".join(x[2] for x in p.get("subs", [])) or "—"
        deco = []
        if p.get("fx"):
            deco.append(f"花字「{p['fx']['text']}」{p['fx'].get('at', .25):.1f}s")
        if p.get("card"):
            deco.append(f"信息卡「{p['card']['title']}」{p['card'].get('at', .3):.1f}s")
        stk = [describe_sticker(s, W) for s in p.get("stickers", [])]
        sfx = [f"{e.get('name') or os.path.basename(e.get('file', ''))} {e.get('at', .03):.1f}s" for e in p.get("sfx", [])]
        t0, t1 = t, t + dur
        rows.append(f"<tr><td><img src='data:image/jpeg;base64,{b64}' alt='片段 {n} 样张'><div class=cap>样张时刻 {km:.1f}s</div></td>"
                    f"<td class=tc><b>{n:02d}</b><br>{t0 / speed:.1f}–{t1 / speed:.1f}s<br><span class=en>原速 {t0:.1f}–{t1:.1f}s</span></td>"
                    f"<td>{html.escape(snd)}<br><span class=en>{html.escape(vid[:40])}</span></td><td>{subs_h or '—'}</td>"
                    f"<td class=fx>{html.escape('；'.join(deco)) or '—'}</td><td>{html.escape('；'.join(stk)) or '—'}</td>"
                    f"<td>{html.escape('、'.join(sfx)) or '—'}</td></tr>")
        md.append(f"| {n} | {t0 / speed:.1f}–{t1 / speed:.1f}s | {snd} | {subs_m} | {'；'.join(deco) or '—'} | "
                  f"{'；'.join(stk) or '—'} | {'、'.join(sfx) or '—'} |")
        t = t1
    removed = tl.get("removed", [])
    rm_html = "".join(f"<li>{html.escape(x)}</li>" for x in removed)
    page = f"""<title>{html.escape(tl.get('title', '分镜'))}</title><meta name="viewport" content="width=device-width">
<style>:root{{--bg:#f6f4f1;--card:#fff;--fg:#1f2326;--mut:#6c7378;--line:#e4e0da;--acc:#e0572a}}
@media (prefers-color-scheme:dark){{:root{{--bg:#15191b;--card:#1e2427;--fg:#eceff1;--mut:#9aa3a8;--line:#30373b}}}}
body{{background:var(--bg);color:var(--fg);font-family:"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;margin:0;padding:24px max(16px,env(safe-area-inset-left))}}
h1{{margin:0 0 4px}} .sub{{color:var(--mut);margin:0 0 12px}} .wrap{{overflow-x:auto}}
table{{border-collapse:collapse;min-width:1100px;background:var(--card)}} td{{border-top:1px solid var(--line);padding:10px;vertical-align:top;font-size:14px}}
img{{width:400px;height:auto;border-radius:6px;display:block}} .cap{{font-size:11px;color:var(--mut);margin-top:4px}}
.tc{{font-family:Menlo,monospace;white-space:nowrap}} .en{{color:var(--mut);font-size:12px}} .fx{{color:var(--acc);font-weight:600}}
.box{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 16px;margin:0 0 16px;max-width:900px}}
.box ul{{margin:6px 0 0;padding-left:1.2em}}</style>
<h1>{html.escape(tl.get('title', '分镜'))}</h1>
<p class=sub>{len(rows)} 个片段 · 原速 {t:.1f}s · {speed:g} 倍速后约 {t / speed:.1f}s · 角标「{html.escape(tl.get('brand', ''))}」。样张是成片里那一刻的真实画面，贴图、花字、信息卡都画在真实位置；动态效果要看成片。</p>
{f"<div class=box><b>剪掉的部分</b><ul>{rm_html}</ul></div>" if removed else ""}
<div class=wrap><table>{''.join(rows)}</table></div>
<div class=box style="margin-top:16px"><b>请确认</b><ul><li>每句字幕是不是你说的话、有没有错字</li><li>贴图、花字、信息卡有没有挡脸，位置和内容合不合适</li><li>剪掉的停顿 / 重复对不对</li></ul>确认后才生成视频。</div>"""
    open(os.path.join(a.out, "storyboard.html"), "w", encoding="utf-8").write(page)
    open(os.path.join(a.out, "storyboard.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))
    print(f"\n分镜页：{os.path.join(a.out, 'storyboard.html')}（{len(rows)} 个片段，原速 {t:.1f}s，{speed:g} 倍速后 {t / speed:.1f}s）")


if __name__ == "__main__":
    main()
