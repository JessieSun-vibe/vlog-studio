"""搭时间线用的小工具（在你为每个项目写的 build_timeline.py 里 import）。

  import sys; sys.path.insert(0, "<skill>/scripts"); from timeline_tools import *
  vo = Transcript("work/transcripts/口播-剪辑版.json")        # 转写结果（带 wav16k 路径）
  cuts = shared_cuts(vo, [[1, 2], [3, 4, 5, 6], [8, 9]])      # 每组 = 一个口播片段用到的段落号
  subs = cue_times(vo, [("中文", "English", [1]), ...], a0=cuts[0][0])

核心规则：前后相接的两个口播片段共用一个切点（两句之间最安静处），不要各自加余量，
否则上一句的尾字会出现在下一句开头。
"""
import array, json, math, re, wave


class Transcript:
    def __init__(self, path):
        self.data = json.load(open(path, encoding="utf-8"))
        self.segs = [s for s in self.data["segments"] if s.get("words")]
        self.wav = self.data.get("wav16k")
        self._x = None

    def seg(self, i):
        w = self.segs[i]["words"]; return w[0]["start"], w[-1]["end"]

    def text(self, i):
        return self.segs[i]["text"].strip()

    def find(self, needle):
        """第一个包含 needle 的段落号。"""
        for i, s in enumerate(self.segs):
            if needle in s["text"]:
                return i
        raise KeyError(needle)

    def word_start(self, i, needle):
        for w in self.segs[i]["words"]:
            if needle in w["word"]:
                return w["start"]
        raise KeyError(needle)

    # ---- 能量 / 安静点 ----
    def _load(self):
        if self._x is None:
            w = wave.open(self.wav); self._sr = w.getframerate()
            self._x = array.array("h", w.readframes(w.getnframes()))

    def quiet_point(self, a, b, step=.02):
        self._load()
        if b - a <= step:
            return (a + b) / 2
        def r(t):
            s = self._x[int(t * self._sr):int((t + step) * self._sr)]
            return math.sqrt(sum(v * v for v in s) / max(1, len(s)))
        return min((r(a + i * step), a + i * step) for i in range(int((b - a) / step)))[1] + step / 2


def shared_cuts(tr, groups):
    """groups: 每个口播片段用到的段落号列表（按时间顺序）。返回每个片段的 (a0, a1)。
    相邻且段落号连续的片段共用切点；不连续（中间删了句子）的各自在安静处切。"""
    n = len(tr.segs); res = []
    for g in groups:
        i0, i1 = min(g), max(g)
        w0, w1 = tr.seg(i0)[0], tr.seg(i1)[1]
        lo = tr.seg(i0 - 1)[1] if i0 > 0 else 0.0
        hi = tr.seg(i1 + 1)[0] if i1 + 1 < n else w1 + .6
        a0 = 0.0 if i0 == 0 else tr.quiet_point(min(lo, w0 - .05) - .1, w0 + .15)
        a1 = tr.quiet_point(w1 - .15, max(hi + .15, w1 + .05))
        res.append([a0, a1, i0, i1])
    for k in range(len(res) - 1):
        if res[k + 1][2] == res[k][3] + 1:          # 下一片段紧接着这一句：共用切点
            res[k + 1][0] = res[k][1]
    return [(round(a, 3), round(b, 3)) for a, b, _, _ in res]


def cue_times(tr, cues, a0, dur=None, lead=.05, tail=.15, fill_gap=.4):
    """cues: [(中文, 英文, [段落号...]), ...] → 片段内相对时间 [(t0, t1, 中文, 英文)]。
    多条字幕共用同一段落时按字数比例分时间；间隔小于 fill_gap 的接上，避免字幕闪烁。"""
    groups = {}
    for k, (_, _, ids) in enumerate(cues):
        key = (tr.seg(min(ids))[0], tr.seg(max(ids))[1]); groups.setdefault(key, []).append(k)
    out = []
    for (s0, s1), ks in groups.items():
        n = sum(len(cues[k][0]) for k in ks); t = s0
        for k in ks:
            t1 = s1 if k == ks[-1] else t + (s1 - s0) * len(cues[k][0]) / n
            out.append([max(0, t - a0 - lead), t1 - a0 + tail, cues[k][0], cues[k][1]]); t = t1
    out.sort()
    for k in range(len(out) - 1):
        if out[k + 1][0] - out[k][1] < fill_gap:
            out[k][1] = out[k + 1][0]
    if dur is not None:
        for c in out:
            c[1] = min(c[1], dur)
    return [tuple(round(v, 3) if isinstance(v, float) else v for v in c) for c in out]


def split_sub(cn, en, width_fn, maxw=1400):
    """中文太宽就按标点拆成几条；英文只在标点后断开，选最接近中文比例的位置。
    width_fn(text) -> 像素宽（用渲染时的中文字体量）。"""
    if width_fn(cn) <= maxw:
        return [(cn, en)]
    pieces = [p for p in re.split(r"(?<=[，。！？：；…])", cn) if p]
    groups, cur = [], ""
    for p in pieces:
        if cur and width_fn(cur + p) > maxw:
            groups.append(cur); cur = p
        else:
            cur += p
    groups.append(cur); groups = [g.rstrip("，、") for g in groups]
    words = en.split(); total = sum(len(g) for g in groups)
    breaks = [k + 1 for k, w in enumerate(words[:-1]) if w[-1] in ",:;.!?—" or words[k + 1] == "—"]
    out, w0, acc = [], 0, 0
    for k, g in enumerate(groups):
        if k == len(groups) - 1:
            w1 = len(words)
        else:
            acc += len(g); target = len(words) * acc / total
            cands = [b for b in breaks if b > w0] or [round(target)]
            w1 = min(cands, key=lambda b: abs(b - target))
        out.append((g, " ".join(words[w0:w1]).strip(" —") or en)); w0 = w1
    return out
