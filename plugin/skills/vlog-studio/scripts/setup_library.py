#!/usr/bin/env python3
"""一键建立素材库：3 款可商用中文字体、128 个动态 / 静态表情贴图（按用途分文件夹）、18 个原创音效，
外加素材清单（每个素材的含义、适合场景、授权）、署名文件和预览页。

  python3 setup_library.py <素材库文件夹> [--update-style ~/.claude/vlog-studio/style.json] [--skip-fonts] [--skip-stickers]

- 字体和贴图从官方源下载（Google Fonts、Google Noto Emoji），约 45MB；音效直接从 skill 自带的 assets/sfx 复制。
- 下载前先征得用户同意。已经存在的文件会跳过，可以重复运行（断网后续传）。
- 加 --update-style：把风格档案里的字体、音效、贴图库、素材清单路径指向这个素材库（没有档案就用模板新建）。
"""
import argparse, hashlib, html, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
MANIFEST = os.path.join(SKILL, "assets", "library_manifest.json")
SFX_KEYS = {"chapter": "切换-switch", "page": "翻页-page", "photo": "快门-shutter", "pop": "啵-pop", "ding": "叮-ding",
            "sparkle": "星光-sparkle", "tada": "揭晓-tada", "success": "成功-success", "oops": "失败-oops",
            "whoosh": "嗖-whoosh", "swoosh": "嗖-短-swoosh", "bubble": "泡泡-bubble", "boing": "弹簧-boing",
            "heartbeat": "心跳-heartbeat", "typing": "打字-typing", "click": "点击-click", "bell": "叮-低-bell"}


def fetch(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return "skip"
    tmp = dest + ".part"
    r = subprocess.run(["curl", "-sSfL", "--retry", "3", "--max-time", "180", "-o", tmp, url], capture_output=True, text=True)
    if r.returncode:
        if os.path.exists(tmp):
            os.remove(tmp)
        return "fail"
    os.replace(tmp, dest); return "ok"


def preview(lib, items):
    fonts = [i for i in items if i["type"] == "字体"]; sfx = [i for i in items if i["type"] == "音效"]
    cats = {}
    for i in items:
        if "贴图" in i["type"]:
            cats.setdefault(i["category"], []).append(i)
    def card(i):
        m = html.escape(i["meaning"]); n = html.escape(i["name"])
        media = (f"<video src='{i['file']}' autoplay loop muted playsinline></video>" if i["file"].endswith(".webm")
                 else f"<img src='{i['file']}' alt='{n}'>")
        return f"<figure title='{m}'>{media}<figcaption><b>{n}</b><span>{m}</span></figcaption></figure>"
    fcss = "".join(f"@font-face{{font-family:'f{k}';src:url('{f['file']}')}}" for k, f in enumerate(fonts))
    frows = "".join(f"<div class=font><p style=\"font-family:'f{k}'\">开启海岛模式！两晚 800 元 9.5/10</p><small>{html.escape(f['meaning'])}</small></div>"
                    for k, f in enumerate(fonts))
    srows = "".join(f"<button type=button data-src='{s['file']}'><b>{html.escape(s['name'])}</b><span>{html.escape(s['meaning'])}</span></button>" for s in sfx)
    secs = "".join(f"<section><h2>{html.escape(c)} <small>{len(v)}</small></h2><div class=grid>{''.join(card(i) for i in v)}</div></section>" for c, v in cats.items())
    page = f"""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width"><title>vlog 素材库</title>
<style>{fcss}
:root{{--bg:#f6f4f1;--card:#fff;--fg:#1f2326;--mut:#6c7378;--line:#e4e0da;--acc:#ff5c8a}}
@media (prefers-color-scheme:dark){{:root{{--bg:#16191b;--card:#1f2427;--fg:#eceff1;--mut:#9aa3a8;--line:#30373b}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font-family:"PingFang SC","Hiragino Sans GB",sans-serif;padding:28px max(16px,env(safe-area-inset-left))}}
h1{{font-family:'f0',sans-serif;font-weight:400;font-size:44px;margin:0;color:var(--acc)}} .lede{{color:var(--mut);margin:6px 0 24px}}
h2{{font-size:18px;margin:28px 0 10px}} h2 small{{color:var(--mut);font-weight:400}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:10px}}
figure{{margin:0;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px;text-align:center}}
figure video,figure img{{width:72px;height:72px;object-fit:contain}}
figcaption b{{display:block;font-size:12px;font-family:Menlo,monospace;word-break:break-all}} figcaption span{{display:block;font-size:12px;color:var(--mut)}}
.sfx{{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:8px}}
button{{font:inherit;text-align:left;background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:10px;padding:10px 12px;cursor:pointer}}
button:hover,button.on{{border-color:var(--acc)}} button b{{display:block}} button span{{font-size:12px;color:var(--mut)}}
.font{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 16px;margin-bottom:8px}} .font p{{font-size:34px;margin:4px 0}} .font small{{color:var(--mut)}}</style>
<h1>vlog 素材库</h1><p class=lede>{len(items)} 项：贴图 {sum(len(v) for v in cats.values())}、音效 {len(sfx)}、字体 {len(fonts)}。鼠标停在贴图上看适合的场景；点音效试听。用 Chrome 打开（Safari 不支持透明 webm）。</p>
<section><h2>字体</h2>{frows}</section><section><h2>音效 <small>{len(sfx)}</small></h2><div class=sfx>{srows}</div></section>{secs}
<script>let a=new Audio();document.querySelectorAll('button[data-src]').forEach(b=>b.onclick=()=>{{document.querySelectorAll('button.on').forEach(x=>x.classList.remove('on'));b.classList.add('on');a.src=b.dataset.src;a.play();}});</script>"""
    open(os.path.join(lib, "素材预览.html"), "w").write(page)


def update_style(path, lib):
    path = os.path.expanduser(path)
    if os.path.exists(path):
        st = json.load(open(path))
    else:
        st = json.load(open(os.path.join(SKILL, "styles", "template.json"))); os.makedirs(os.path.dirname(path), exist_ok=True)
    f = lambda n: os.path.join(lib, "字体", n)
    st.setdefault("fonts", {})
    if os.path.exists(f("ZCOOLKuaiLe-Regular.ttf")):
        st["fonts"]["fun"] = st["fonts"]["brand"] = f("ZCOOLKuaiLe-Regular.ttf")
    if os.path.exists(f("ZCOOLQingKeHuangYou-Regular.ttf")):
        st["fonts"]["title"] = f("ZCOOLQingKeHuangYou-Regular.ttf")
    if os.path.exists(f("LongCang-Regular.ttf")):
        st["fonts"]["hand"] = f("LongCang-Regular.ttf")
    st["sfx"] = {k: os.path.join(lib, "音效", v + ".wav") for k, v in SFX_KEYS.items() if os.path.exists(os.path.join(lib, "音效", v + ".wav"))}
    st["library"] = lib; st["stickers_dir"] = os.path.join(lib, "贴图"); st["asset_catalog"] = os.path.join(lib, "素材清单.json")
    json.dump(st, open(path, "w"), ensure_ascii=False, indent=2)
    print(f"风格档案已更新：{path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("library"); ap.add_argument("--update-style")
    ap.add_argument("--skip-fonts", action="store_true"); ap.add_argument("--skip-stickers", action="store_true")
    a = ap.parse_args()
    lib = os.path.abspath(os.path.expanduser(a.library)); m = json.load(open(MANIFEST))
    for d in ("字体", "贴图", "音效"):
        os.makedirs(os.path.join(lib, d), exist_ok=True)
    items, stat = [], {"ok": 0, "skip": 0, "fail": 0}; fails = []
    if not a.skip_fonts:
        for f in m["fonts"]:
            dest = os.path.join(lib, "字体", f["name"] + ".ttf"); r = fetch(f["url"], dest); stat[r] += 1
            fetch(f["license_url"], os.path.join(lib, "字体", f"OFL-{f['name']}.txt"))
            if r == "fail":
                fails.append(f["name"])
            if os.path.exists(dest):
                items.append({"type": "字体", "category": "字体", "name": f["name"], "meaning": f["meaning"],
                              "file": f"字体/{f['name']}.ttf", "license": f["license"]})
    if not a.skip_stickers:
        n = len(m["stickers"])
        for k, s in enumerate(m["stickers"], 1):
            cdir = os.path.join(lib, "贴图", s["category"]); os.makedirs(cdir, exist_ok=True)
            dest = os.path.join(cdir, f"{s['name']}.{s['kind']}"); r = fetch(s["url"], dest); stat[r] += 1
            if r == "fail":
                fails.append(s["name"])
            if k % 20 == 0 or k == n:
                print(f"贴图 {k}/{n}", flush=True)
            if os.path.exists(dest):
                items.append({"type": "动态贴图" if s["kind"] == "webm" else "静态贴图", "category": s["category"], "name": s["name"],
                              "meaning": s["meaning"], "file": f"贴图/{s['category']}/{s['name']}.{s['kind']}", "license": s["license"],
                              "source": s["url"], "sha256_16": hashlib.sha256(open(dest, "rb").read()).hexdigest()[:16],
                              "status": "已下载，待在成片里确认"})
        static = os.path.join(lib, "贴图", "静态图标")
        if os.path.isdir(static):
            fetch("https://www.apache.org/licenses/LICENSE-2.0.txt", os.path.join(static, "LICENSE-Apache-2.0.txt"))
    for s in m["sfx"]:
        src = os.path.join(SKILL, "assets", "sfx", s["file"]); dest = os.path.join(lib, "音效", s["file"])
        if not os.path.exists(dest):
            shutil.copy2(src, dest)
        items.append({"type": "音效", "category": "音效", "name": s["name"], "meaning": s["meaning"], "file": f"音效/{s['file']}", "license": s["license"]})
    shutil.copy2(os.path.join(SKILL, "assets", "sfx", "生成音效.py"), os.path.join(lib, "音效", "生成音效.py"))
    json.dump(items, open(os.path.join(lib, "素材清单.json"), "w"), ensure_ascii=False, indent=1)
    open(os.path.join(lib, "CREDITS.md"), "w").write(
        "# 素材署名（发布视频时可复制）\n\n动态表情贴图：Google Noto Emoji Animation（CC BY 4.0）https://googlefonts.github.io/noto-emoji-animation/\n"
        "静态表情图标：Google Noto Emoji（Apache-2.0）https://github.com/googlefonts/noto-emoji\n"
        "字体：站酷快乐体、站酷庆科黄油体、龙藏体（SIL Open Font License 1.1）\n音效：vlog-studio 原创合成\n\n"
        "小红书 / 抖音正文末尾可写：「贴图：Google Noto Emoji（CC BY 4.0）」\n")
    open(os.path.join(lib, "README.md"), "w").write(
        "# vlog 素材库\n\n由 vlog-studio 的 setup_library.py 建立。风格档案指向这里，别挪动这个文件夹；要挪的话告诉 AI 更新风格档案。\n\n"
        "- `素材预览.html`：用 Chrome 打开，贴图会动、音效能试听。\n- `素材清单.json`：每个素材的含义、适合场景、授权，剪片时 AI 按它挑。\n"
        "- `CREDITS.md`：发布时要附的署名。\n- 加新贴图：`fetch_stickers.py 贴图/<分类> <名字...>`，再重跑 setup_library.py 更新清单和预览。\n")
    preview(lib, items)
    if a.update_style:
        update_style(a.update_style, lib)
    print(f"完成：{lib}\n  下载 {stat['ok']}，已有跳过 {stat['skip']}，失败 {stat['fail']}；清单 {len(items)} 项")
    if fails:
        print("  下载失败（网络问题可以重跑本脚本续传）：" + "、".join(fails)); sys.exit(1)


if __name__ == "__main__":
    main()
