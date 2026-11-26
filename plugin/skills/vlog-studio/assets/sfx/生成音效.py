#!/usr/bin/env python3
"""用 ffmpeg 合成一套 vlog 常用音效（全部原创合成，没有授权问题）。
运行：python3 生成音效.py      → 在本文件夹生成 *.wav（48kHz 立体声，峰值约 -3dB）
想改音色就改下面的表达式，再运行一次。
"""
import os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
PI = "PI"

# 名字: (时长秒, ffmpeg 输入, 额外滤镜)
def sine(expr, d):
    return ["-f", "lavfi", "-i", f"aevalsrc='{expr}':s={SR}:d={d}"]


def noise(color, d):
    return ["-f", "lavfi", "-i", f"anoisesrc=color={color}:sample_rate={SR}:duration={d}:amplitude=0.8"]


def bell(f, t0, decay=7, amp=0.5):
    """一个从 t0 开始的钟声音（基频 + 两个泛音）。"""
    return (f"if(gte(t,{t0}),{amp}*exp(-{decay}*(t-{t0}))*(sin(2*{PI}*{f}*(t-{t0}))"
            f"+0.35*sin(2*{PI}*{f*2}*(t-{t0}))+0.12*sin(2*{PI}*{f*3}*(t-{t0}))),0)")


def click(t0, f=3200, amp=.8, decay=260):
    return f"if(gte(t,{t0}),{amp}*exp(-{decay}*(t-{t0}))*sin(2*{PI}*{f}*(t-{t0})),0)"


SFX = {
    "啵-pop":        (.14, sine(f"0.6*sin(2*{PI}*(1400-9000*t)*t)*exp(-38*t)", .14), ""),
    "啵-高-pop-high": (.12, sine(f"0.6*sin(2*{PI}*(2400-14000*t)*t)*exp(-45*t)", .12), ""),
    "叮-ding":       (1.2, sine(bell(1318, 0, 5, .6), 1.2), ""),
    "叮-低-bell":     (1.6, sine(bell(660, 0, 3.5, .6), 1.6), ""),
    "星光-sparkle":   (1.0, sine("+".join(bell(f, t0, 9, .32) for f, t0 in
                                         [(2093, 0), (2637, .07), (3136, .14), (4186, .21)]), 1.0), ""),
    "揭晓-tada":      (1.4, sine("+".join(bell(f, t0, 2.8, .3) for f, t0 in
                                         [(523, 0), (659, .06), (784, .12), (1047, .18)]), 1.4), ""),
    "成功-success":   (.6, sine(bell(880, 0, 9, .5) + "+" + bell(1320, .12, 7, .5), .6), ""),
    "失败-oops":      (.7, sine(f"0.45*exp(-5*t)*sin(2*{PI}*(if(lt(t,.18),440,330))*t)", .7), "lowpass=f=2000"),
    "点击-click":     (.05, sine(click(0), .05), ""),
    "切换-switch":    (.16, sine(click(0, 2600) + "+" + click(.07, 3600, .7), .16), ""),
    "打字-typing":    (.9, sine("+".join(click(t0, f, .5, 320) for t0, f in
                                         [(0, 2800), (.11, 3300), (.19, 3000), (.33, 3500), (.41, 2900),
                                          (.56, 3200), (.63, 3400), (.78, 3000)]), .9), ""),
    "泡泡-bubble":    (.6, sine("+".join(f"if(gte(t,{t0}),0.4*exp(-25*(t-{t0}))*sin(2*{PI}*({f}+5000*(t-{t0}))*(t-{t0})),0)"
                                         for t0, f in [(0, 420), (.13, 560), (.27, 480)]), .6), ""),
    "弹簧-boing":     (.7, sine(f"0.5*exp(-4*t)*sin(2*{PI}*(260+90*sin(2*{PI}*12*t)*exp(-3*t))*t)", .7), ""),
    "心跳-heartbeat": (1.6, sine("+".join(f"if(gte(t,{t0}),0.9*exp(-28*(t-{t0}))*sin(2*{PI}*55*(t-{t0})),0)"
                                          for t0 in (0, .2, .8, 1.0)), 1.6), "lowpass=f=200"),
    "嗖-whoosh":      (.6, noise("pink", .6), "highpass=f=300,lowpass=f=5000,volume='sin(PI*t/0.6)^2':eval=frame"),
    "嗖-短-swoosh":    (.28, noise("white", .28), "highpass=f=1200,lowpass=f=7000,volume='sin(PI*t/0.28)^3':eval=frame"),
    "翻页-page":      (.32, noise("white", .32), "highpass=f=1800,volume='exp(-9*t)*(0.6+0.4*sin(2*PI*38*t))':eval=frame"),
    "快门-shutter":   (.25, noise("white", .25), "highpass=f=900,volume='exp(-70*t)+if(gte(t,0.09),exp(-60*(t-0.09)),0)':eval=frame"),
}


def main():
    for name, (d, src, af) in SFX.items():
        out = os.path.join(HERE, f"{name}.wav")
        chain = (af + "," if af else "") + f"afade=t=out:st={max(0, d - .02):.3f}:d=0.02,aformat=channel_layouts=stereo"
        subprocess.run(["ffmpeg", "-v", "error", "-y", *src, "-af", chain, "-ar", str(SR), out], check=True)
        # 峰值归一到 -3dB
        r = subprocess.run(["ffmpeg", "-i", out, "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True).stderr
        peak = float(r.split("max_volume:")[1].split("dB")[0])
        tmp = out + ".tmp.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", out, "-af", f"volume={-3 - peak}dB", tmp], check=True)
        os.replace(tmp, out)
        print(f"OK {name}  {d}s")


if __name__ == "__main__":
    main()
