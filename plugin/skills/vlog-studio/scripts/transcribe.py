#!/usr/bin/env python3
"""本地语音转写（Apple 芯片 Mac：mlx-whisper large-v3-turbo），带词级时间。

用法：
  uv run --with mlx-whisper python transcribe.py <工作目录> <音频或视频...> [--prompt "专有名词"] [--lang zh]
每个输入生成 <工作目录>/transcripts/<名字>.json（whisper 原始结果）和 .txt（逐段时间 + 文字），
同时生成 16k 单声道 wav（<名字>_16k.wav），后面算安静切点、看能量图都用它。

注意：
- 第一次运行会下载依赖（torch 等几百 MB）和模型（约 1.5GB），网速慢时先测速。
- 识别会把同一句的重复合并、把专有名词听错（巴厘岛→巴黎岛、Fried→Fair）。字幕要人工改正，重复要看能量图确认。
"""
import argparse, json, os, subprocess

MODEL = "mlx-community/whisper-large-v3-turbo"


def to16k(src, dst):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-map", "0:a:0", "-ac", "1", "-ar", "16000", dst], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workdir"); ap.add_argument("inputs", nargs="+")
    ap.add_argument("--prompt", default=""); ap.add_argument("--lang", default="zh")
    a = ap.parse_args()
    import mlx_whisper
    out = os.path.join(a.workdir, "transcripts"); os.makedirs(out, exist_ok=True)
    for src in a.inputs:
        name = os.path.splitext(os.path.basename(src))[0].replace(" ", "_")
        wav = os.path.join(out, f"{name}_16k.wav")
        if not src.endswith("_16k.wav"):
            to16k(src, wav)
        else:
            wav = src
        r = mlx_whisper.transcribe(wav, path_or_hf_repo=MODEL, language=a.lang, word_timestamps=True,
                                   condition_on_previous_text=False, initial_prompt=a.prompt or None)
        r["source"] = os.path.abspath(src); r["wav16k"] = os.path.abspath(wav)
        json.dump(r, open(os.path.join(out, f"{name}.json"), "w"), ensure_ascii=False, indent=1)
        lines = []
        for i, s in enumerate(r["segments"]):
            w = s.get("words") or []
            if w:
                lines.append(f"{i:3d} {w[0]['start']:7.2f}-{w[-1]['end']:7.2f} {s['text'].strip()}")
        open(os.path.join(out, f"{name}.txt"), "w").write("\n".join(lines) + "\n")
        print(f"== {name}"); print("\n".join(lines) if lines else "（没有识别到人声）")


if __name__ == "__main__":
    main()
