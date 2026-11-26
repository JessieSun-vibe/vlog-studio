#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "mlx-whisper; sys_platform == 'darwin' and platform_machine == 'arm64'",
#   "faster-whisper>=1.1; sys_platform != 'darwin' or platform_machine != 'arm64'",
# ]
# ///
"""本地语音转写，带词级时间。按电脑自动选引擎，输出格式完全一样：

- Apple 芯片 Mac：mlx-whisper（whisper-large-v3-turbo，用 GPU，最快）
- Intel Mac / Windows / Linux：faster-whisper（同一个 large-v3-turbo 模型；有 NVIDIA 显卡用 CUDA，否则用 CPU）

用法（uv 会按电脑自动装对应的依赖）：
  uv run scripts/transcribe.py <工作目录> <音频或视频...> [--prompt "专有名词"] [--lang zh] [--engine auto|mlx|faster]
每个输入生成 <工作目录>/transcripts/<名字>.json（whisper 格式结果）和 .txt（逐段时间 + 文字），
同时生成 16k 单声道 wav（<名字>_16k.wav），后面算安静切点、看能量图都用它。

注意：
- 第一次运行会下载依赖（几百 MB）和模型（约 1.5GB），网速慢时先测速。
- 没有 Apple 芯片、也没有 NVIDIA 显卡时用 CPU 转写，会比较慢（大约和音频时长差不多，甚至更久），属于正常。
- 识别会把同一句的重复合并、把专有名词听错（巴厘岛→巴黎岛、Fried→Fair）。字幕要人工改正，重复要看能量图确认。
"""
import argparse, json, os, platform, subprocess, sys

MLX_MODEL = "mlx-community/whisper-large-v3-turbo"
FASTER_MODEL = "mobiuslabsgmbh/faster-whisper-large-v3-turbo"


def apple_silicon():
    return platform.system() == "Darwin" and platform.machine() == "arm64"


def to16k(src, dst):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-map", "0:a:0", "-ac", "1", "-ar", "16000", dst], check=True)


def mlx_engine(lang, prompt):
    import mlx_whisper

    def run(wav):
        return mlx_whisper.transcribe(wav, path_or_hf_repo=MLX_MODEL, language=lang, word_timestamps=True,
                                      condition_on_previous_text=False, initial_prompt=prompt or None)
    return "mlx-whisper", run


def faster_engine(lang, prompt):
    from faster_whisper import WhisperModel
    device, compute = "cpu", "int8"
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() > 0:
            device, compute = "cuda", "float16"
    except Exception:  # noqa: BLE001
        pass
    try:
        model = WhisperModel(FASTER_MODEL, device=device, compute_type=compute)
    except Exception as e:  # noqa: BLE001  CUDA 库不全时退回 CPU
        if device == "cpu":
            raise
        print(f"⚠️ 显卡加速没启动（{e}），改用 CPU", file=sys.stderr)
        device, compute = "cpu", "int8"
        model = WhisperModel(FASTER_MODEL, device=device, compute_type=compute)

    def run(wav):
        # 自己读 16k 单声道 wav 交给模型，不走 faster-whisper 内置的 PyAV 解码（版本不配套时会报错）
        import wave
        import numpy as np
        with wave.open(wav) as w:
            pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
        audio = pcm.astype(np.float32) / 32768.0
        segs, info = model.transcribe(audio, language=lang, word_timestamps=True,
                                      condition_on_previous_text=False, initial_prompt=prompt or None)
        out = []
        for i, s in enumerate(segs):
            out.append({"id": i, "start": s.start, "end": s.end, "text": s.text,
                        "words": [{"word": w.word, "start": w.start, "end": w.end, "probability": w.probability}
                                  for w in (s.words or [])]})
        return {"text": "".join(s["text"] for s in out), "segments": out, "language": info.language}
    return f"faster-whisper（{device}）", run


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workdir"); ap.add_argument("inputs", nargs="+")
    ap.add_argument("--prompt", default=""); ap.add_argument("--lang", default="zh")
    ap.add_argument("--engine", choices=["auto", "mlx", "faster"], default="auto",
                    help="默认按电脑自动选；faster 可以在 Apple 芯片 Mac 上测试其他电脑的转写路径")
    a = ap.parse_args()
    use_mlx = a.engine == "mlx" or (a.engine == "auto" and apple_silicon())
    try:
        engine, transcribe = (mlx_engine if use_mlx else faster_engine)(a.lang, a.prompt)
    except ImportError as e:
        need = "mlx-whisper" if use_mlx else "faster-whisper"
        raise SystemExit(f"缺少 {need}（{e}）。请用 `uv run scripts/transcribe.py ...` 运行，uv 会自动装好；"
                         f"或者 `uv run --with {need} python scripts/transcribe.py ...`")
    print(f"转写引擎：{engine}", flush=True)
    out = os.path.join(a.workdir, "transcripts"); os.makedirs(out, exist_ok=True)
    for src in a.inputs:
        name = os.path.splitext(os.path.basename(src))[0].replace(" ", "_")
        wav = os.path.join(out, f"{name}_16k.wav")
        if not src.endswith("_16k.wav"):
            to16k(src, wav)
        else:
            wav = src
        r = transcribe(wav)
        r["source"] = os.path.abspath(src); r["wav16k"] = os.path.abspath(wav); r["engine"] = engine
        json.dump(r, open(os.path.join(out, f"{name}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        lines = []
        for i, s in enumerate(r["segments"]):
            w = s.get("words") or []
            if w:
                lines.append(f"{i:3d} {w[0]['start']:7.2f}-{w[-1]['end']:7.2f} {s['text'].strip()}")
        open(os.path.join(out, f"{name}.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
        print(f"== {name}"); print("\n".join(lines) if lines else "（没有识别到人声）")


if __name__ == "__main__":
    main()
