#!/usr/bin/env python3
"""清理人声：找停顿 / 疑似重复 / 拖长的字，按切点剪音频。

  python3 clean_speech.py report <转写.json> [--pause 0.4]
      列出：超过 pause 秒的停顿（建议切点）、一个字超过 0.6s 的地方（常常是重复被识别器合并了）、
      相邻两段文字高度相似的地方（同一句说了两遍）。并写出 <转写>_cuts_suggested.json。
  python3 clean_speech.py energy <16k.wav> <开始秒> <结束秒>
      每 50ms 一行的能量图，用来看清哪里有字、哪里是空白，确认重复的边界。
  python3 clean_speech.py quiet <16k.wav> <开始秒> <结束秒>
      找这段里最安静的 20ms 的中点（切点要放在这里）。
  python3 clean_speech.py apply <原音频> <cuts.json> <输出.wav>
      cuts.json = [[开始秒, 结束秒], ...]（要删掉的段）。每个拼接点 10ms 淡入淡出，输出 24bit wav，
      同时写 <输出>.edl.json 记录切点，方便回溯。
剪完一定重新转写输出文件核对。
"""
import array, difflib, json, math, os, subprocess, sys, wave
for _s in (sys.stdout, sys.stderr):  # 英文版 Windows 的终端不是 UTF-8，打印中文会报错
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")


def load16k(path):
    w = wave.open(path); sr = w.getframerate()
    return array.array("h", w.readframes(w.getnframes())), sr


def rms_db(x, sr, t, step):
    s = x[int(t * sr):int((t + step) * sr)]
    if not s:
        return -90.0
    r = math.sqrt(sum(v * v for v in s) / len(s))
    return 20 * math.log10(r / 32768 + 1e-9)


def quiet_point(x, sr, a, b, step=0.02):
    if b - a <= step:
        return (a + b) / 2
    return min((rms_db(x, sr, a + i * step, step), a + i * step) for i in range(int((b - a) / step)))[1] + step / 2


def report(tjson, pause):
    r = json.load(open(tjson, encoding="utf-8")); words = [w for s in r["segments"] for w in s.get("words", [])]
    cuts = []
    print("== 停顿（建议缩到约 0.18s）")
    for p, q in zip(words, words[1:]):
        gap = q["start"] - p["end"]
        if gap > pause:
            print(f"  {p['end']:7.2f}-{q['start']:7.2f} ({gap:.2f}s)  …{p['word']} | {q['word']}")
            cuts.append([round(p["end"] + .09, 3), round(q["start"] - .09, 3)])
    print("== 拖长的字（>1.0s，很可能是重复被识别器合并了，用 energy 看能量图确认）")
    for w in words:
        if w["end"] - w["start"] > 1.0:
            print(f"  {w['start']:7.2f}-{w['end']:7.2f} 「{w['word']}」 {w['end']-w['start']:.2f}s")
    print("== 疑似重复（相邻两段很像，通常保留后一遍）")
    segs = [s for s in r["segments"] if s.get("words")]
    for s1, s2 in zip(segs, segs[1:]):
        a, b = s1["text"].strip(), s2["text"].strip()
        if a and b and difflib.SequenceMatcher(None, a, b).ratio() > .6:
            print(f"  {s1['words'][0]['start']:7.2f} 「{a}」 ≈ {s2['words'][0]['start']:7.2f} 「{b}」")
    out = os.path.splitext(tjson)[0] + "_cuts_suggested.json"
    json.dump(cuts, open(out, "w", encoding="utf-8")); print(f"\n停顿切点建议已写到 {out}（只含停顿；重复要自己确认后加进去）")


def energy(wav, a, b):
    x, sr = load16k(wav)
    t = a
    while t < b:
        db = rms_db(x, sr, t, .05)
        print(f"{t:7.2f} {db:6.1f} {'#' * max(0, int((db + 60) / 1.5))}"); t += .05


def apply(src, cuts_json, out):
    cuts = sorted(json.load(open(cuts_json, encoding="utf-8")))
    dur = float(json.loads(subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", src],
                                          capture_output=True, text=True).stdout)["format"]["duration"])
    keep, t = [], 0.0
    for a, b in cuts:
        if a > t:
            keep.append((t, a))
        t = max(t, b)
    keep.append((t, dur))
    fc, lab = [], []
    for i, (a, b) in enumerate(keep):
        fc.append(f"[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,"
                  f"afade=t=out:st={max(0, b - a - .012):.3f}:d=0.012[k{i}]"); lab.append(f"[k{i}]")
    fc.append(f"{''.join(lab)}concat=n={len(keep)}:v=0:a=1[o]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", ";".join(fc), "-map", "[o]",
                    "-c:a", "pcm_s24le", out], check=True)
    json.dump({"source": os.path.abspath(src), "cuts": cuts, "keep": keep}, open(out + ".edl.json", "w", encoding="utf-8"), indent=1)
    new = sum(b - a for a, b in keep)
    print(f"{dur:.1f}s -> {new:.1f}s（删掉 {dur - new:.1f}s，{len(keep)} 段）")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "report":
        pause = float(sys.argv[sys.argv.index("--pause") + 1]) if "--pause" in sys.argv else .4
        report(sys.argv[2], pause)
    elif cmd == "energy":
        energy(sys.argv[2], float(sys.argv[3]), float(sys.argv[4]))
    elif cmd == "quiet":
        x, sr = load16k(sys.argv[2]); print(round(quiet_point(x, sr, float(sys.argv[3]), float(sys.argv[4])), 3))
    elif cmd == "apply":
        apply(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print(__doc__)
