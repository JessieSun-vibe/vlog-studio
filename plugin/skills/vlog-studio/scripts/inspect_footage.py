#!/usr/bin/env python3
"""看素材：列出文件信息 + 每段视频的带时间码缩略图总表；照片按 EXIF 转正。

用法：
  uv run --with pillow python inspect_footage.py <素材文件夹> --out <输出目录> [--step 2]
  uv run --with pillow python inspect_footage.py --sheet <成片.mp4> --out <输出目录> [--step 4]   # 成片自查
需要 ffmpeg / ffprobe 和 Pillow（uv run --with pillow python ...）；macOS 自带 sips 用来转正照片。
"""
import argparse, json, os, subprocess, sys

VIDEO = {".mov", ".mp4", ".m4v", ".avi", ".mkv"}
PHOTO = {".jpg", ".jpeg", ".heic", ".png"}
AUDIO = {".m4a", ".wav", ".mp3", ".aac", ".caf"}


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path],
                       capture_output=True, text=True)
    return json.loads(r.stdout or "{}")


def describe(path):
    info = probe(path); fmt = info.get("format", {})
    v = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), None)
    a = [s for s in info.get("streams", []) if s.get("codec_type") == "audio"]
    d = {"file": os.path.basename(path), "duration": round(float(fmt.get("duration", 0) or 0), 2)}
    if v:
        w, h = int(v.get("width", 0)), int(v.get("height", 0))
        rot = 0
        for sd in v.get("side_data_list", []) or []:
            rot = int(sd.get("rotation", 0) or 0)
        if abs(rot) == 90:
            w, h = h, w
        d.update(width=w, height=h, orientation="横屏" if w > h else ("竖屏" if h > w else "方形"),
                 fps=v.get("r_frame_rate"), codec=v.get("codec_name"))
    d["audio_tracks"] = len(a)
    return d


def sheet(path, out_png, step, cols=6, width=320):
    """每 step 秒一帧，拼成总表，每张左上角印时间码（需要 Pillow）。"""
    import math, shutil, tempfile
    from PIL import Image, ImageDraw, ImageFont
    tmp = tempfile.mkdtemp()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-vf", f"fps=1/{step},scale={width}:-2",
                    os.path.join(tmp, "f%04d.jpg")], check=True)
    files = sorted(os.listdir(tmp))
    if not files:
        return []
    first = Image.open(os.path.join(tmp, files[0])); w, h = first.size
    rows = math.ceil(len(files) / cols)
    out = Image.new("RGB", (cols * w, rows * h), "black"); d = ImageDraw.Draw(out)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 16)
    except OSError:
        font = ImageFont.load_default()
    times = []
    for k, f in enumerate(files):
        x, y = (k % cols) * w, (k // cols) * h; t = k * step + step / 2   # fps 滤镜取的是每段中间的帧
        out.paste(Image.open(os.path.join(tmp, f)), (x, y))
        d.rectangle([x, y, x + 74, y + 22], fill=(0, 0, 0)); d.text((x + 4, y + 3), f"{t:5.1f}s", fill=(255, 230, 0), font=font)
        times.append(round(t, 1))
    out.save(out_png, quality=85); shutil.rmtree(tmp)
    return times


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", nargs="?")
    ap.add_argument("--out", required=True)
    ap.add_argument("--step", type=float, default=2.0)
    ap.add_argument("--sheet", help="只给一个视频出总表（成片自查用）")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if a.sheet:
        d = describe(a.sheet); step = a.step or max(1.0, d["duration"] / 30)
        p = os.path.join(a.out, "sheet_" + os.path.splitext(os.path.basename(a.sheet))[0] + ".jpg")
        sheet(a.sheet, p, step)
        print(json.dumps({**d, "sheet": p, "seconds_per_tile": step, "layout": "6 列，每张左上角有时间码"}, ensure_ascii=False, indent=1))
        return
    rows = []
    for name in sorted(os.listdir(a.folder)):
        path = os.path.join(a.folder, name); ext = os.path.splitext(name)[1].lower()
        if name.startswith(".") or not os.path.isfile(path):
            continue
        if ext in VIDEO:
            d = describe(path)
            p = os.path.join(a.out, f"sheet_{os.path.splitext(name)[0][:40]}.jpg")
            step = a.step if d["duration"] <= 96 else d["duration"] / 48
            sheet(path, p, step); d.update(kind="video", sheet=p, seconds_per_tile=round(step, 2))
        elif ext in PHOTO:
            p = os.path.join(a.out, f"photo_{os.path.splitext(name)[0][:40]}.jpg")
            subprocess.run(["sips", "-Z", "1200", "-s", "format", "jpeg", path, "--out", p], capture_output=True)
            d = {"file": name, "kind": "photo", "preview": p}
            r = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", p], capture_output=True, text=True).stdout
            nums = [int(x.split()[-1]) for x in r.splitlines() if "pixel" in x]
            if len(nums) == 2:
                d["orientation"] = "横" if nums[0] > nums[1] else "竖"
        elif ext in AUDIO:
            d = {**describe(path), "kind": "audio"}
        else:
            continue
        rows.append(d)
    json.dump(rows, open(os.path.join(a.out, "footage.json"), "w"), ensure_ascii=False, indent=1)
    for d in rows:
        print(json.dumps(d, ensure_ascii=False))
    print("\n总表每张左上角印了时间码。逐张看清每段几秒拍了什么。", file=sys.stderr)


if __name__ == "__main__":
    main()
