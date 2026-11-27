#!/usr/bin/env python3
"""整片变速：画面 setpts、声音 atempo（音调不变），SRT 时间同步缩放，并报告读不完的字幕。

  python3 speedup.py <成片.mp4> <成片.srt> 1.2 [输出.mp4]
"""
import re, subprocess, sys
for _s in (sys.stdout, sys.stderr):  # 英文版 Windows 的终端不是 UTF-8，打印中文会报错
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")


def main():
    src, srt, k = sys.argv[1], sys.argv[2], float(sys.argv[3])
    out = sys.argv[4] if len(sys.argv) > 4 else src.replace(".mp4", f"-{k:g}倍速.mp4")
    tempo = []; r = k
    while r > 2.0:
        tempo.append("atempo=2.0"); r /= 2.0
    tempo.append(f"atempo={r}")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex",
                    f"[0:v]setpts=PTS/{k},fps=30[v];[0:a]{','.join(tempo)},loudnorm=I=-16:TP=-1.5[a]",
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", out], check=True)

    def conv(m):
        h, mi, s, ms = map(int, m.groups()); t = (h * 3600 + mi * 60 + s + ms / 1000) / k
        ms = int(round(t * 1000)); return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    text = re.sub(r"(\d\d):(\d\d):(\d\d),(\d\d\d)", conv, open(srt, encoding="utf-8").read())
    out_srt = out.rsplit(".", 1)[0] + ".srt"; open(out_srt, "w", encoding="utf-8").write(text)

    def sec(x):
        h, m, r_ = x.split(":"); s, ms = r_.split(","); return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
    warn = []
    for b in text.strip().split("\n\n"):
        L = b.split("\n"); a, c = L[1].split(" --> "); d = sec(c) - sec(a)
        n = len(re.findall(r"[一-鿿]", L[2]))
        if d < .8 or (d and n / d > 7):
            warn.append(f"  {d:.2f}s  {n / d if d else 0:.1f}字/秒  {L[2]}")
    print(f"完成：{out}\n字幕：{out_srt}")
    if warn:
        print("可能读不完的字幕：\n" + "\n".join(warn))


if __name__ == "__main__":
    main()
