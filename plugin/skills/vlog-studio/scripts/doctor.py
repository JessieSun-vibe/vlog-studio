#!/usr/bin/env python3
"""安装自检：这台电脑能不能跑 vlog-studio，缺什么、怎么补。

  python3 doctor.py              只检查，打印结果和修复命令（不改任何东西）
  python3 doctor.py --prefetch   检查通过后，提前下载 Python 依赖、语音识别模型（约 1.5GB）和人脸检测模型，
                                 让第一次剪片不用再等。下载前 AI 应先告诉用户大小并征得同意。

退出码 0 = 可以用；1 = 有必须先修的问题（看输出里的「怎么修」）。
"""
import json, os, platform, shutil, subprocess, sys

OK, WARN, BAD = "✅", "⚠️", "❌"
rows, must_fix = [], False


def say(mark, item, detail="", fix=""):
    global must_fix
    rows.append((mark, item, detail, fix))
    if mark == BAD:
        must_fix = True


def run(cmd, timeout=60):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:  # noqa: BLE001
        return 1, str(e)


def check():
    mac = platform.system() == "Darwin"; arm = platform.machine() in ("arm64", "aarch64")
    if mac and arm:
        say(OK, "电脑", f"macOS {platform.mac_ver()[0]} · Apple 芯片：全部功能可用")
    elif mac:
        say(WARN, "电脑", "Intel 芯片的 Mac：本地语音转写（mlx-whisper）不可用，其余功能可用",
            "需要转写时可以改用 openai-whisper / faster-whisper，或在剪映里识别字幕")
    else:
        say(WARN, "电脑", f"{platform.system()}：只在 Apple 芯片 Mac 上完整测试过，本地转写不可用", "")
    brew = shutil.which("brew")
    if mac and not brew:
        say(WARN, "Homebrew", "没装（用来装 ffmpeg / uv）",
            '请用户自己在终端运行（要输入电脑密码，AI 不要代为运行）：/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
    ff = shutil.which("ffmpeg")
    if not ff:
        say(BAD, "ffmpeg", "没装", "brew install ffmpeg")
    else:
        _, v = run(["ffmpeg", "-version"]); ver = (v.split()[2] if len(v.split()) > 2 else "?")
        _, dec = run(["ffmpeg", "-hide_banner", "-decoders"])
        if " libvpx " in dec or "libvpx VP8" in dec:
            say(OK, "ffmpeg", f"{ver}，带 libvpx（能读透明动态贴图）")
        else:
            say(WARN, "ffmpeg", f"{ver}，没有 libvpx：动态贴图会没有透明背景",
                "brew reinstall ffmpeg（Homebrew 版自带 libvpx；如果用的是别处装的 ffmpeg，先 brew install ffmpeg 并确认 which ffmpeg 指向 /opt/homebrew/bin/ffmpeg）")
    if shutil.which("ffprobe"):
        say(OK, "ffprobe", "有")
    else:
        say(BAD, "ffprobe", "没装（随 ffmpeg 一起装）", "brew install ffmpeg")
    if shutil.which("uv"):
        _, v = run(["uv", "--version"]); say(OK, "uv", v.strip())
    else:
        say(BAD, "uv", "没装（用来自动装 Python 依赖）", "brew install uv")
    say(OK, "Python", f"{platform.python_version()}（脚本由 uv 用自己的 Python 运行，系统版本不要紧）")
    style = os.path.expanduser("~/.claude/vlog-studio/style.json")
    if os.path.exists(style):
        st = json.load(open(style)); lib = st.get("library")
        say(OK, "风格档案", style)
        if lib and os.path.isdir(lib):
            say(OK, "素材库", lib)
        else:
            say(WARN, "素材库", "还没建", "python3 scripts/setup_library.py <素材库文件夹> --update-style ~/.claude/vlog-studio/style.json")
    else:
        say(WARN, "风格档案", "还没有（第一次剪片时 AI 会问你几个问题再建）", "")
    hf = os.path.expanduser("~/.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo")
    say(OK if os.path.isdir(hf) else WARN, "语音识别模型", "已下载" if os.path.isdir(hf) else "还没下载（约 1.5GB，第一次转写时自动下）",
        "" if os.path.isdir(hf) else "python3 scripts/doctor.py --prefetch")


def prefetch():
    here = os.path.dirname(os.path.abspath(__file__))
    print("\n== 预先下载依赖和模型（网速慢时会比较久）==", flush=True)
    steps = [
        ("渲染依赖（Pillow、resvg）", ["uv", "run", "--quiet", "--with", "pillow", "--with", "resvg-py", "python", "-c", "import PIL, resvg_py"]),
        ("人脸检测（OpenCV + YuNet 模型）", ["uv", "run", "--quiet", "--with", "opencv-python", "python", "-c",
                                       f"import sys; sys.path.insert(0, {here!r}); import face_track; face_track.detector(960, 540)"]),
    ]
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        steps.append(("语音识别（mlx-whisper 等依赖约 0.5GB + 模型约 1.5GB）", ["uv", "run", "--quiet", "--with", "mlx-whisper", "python", "-c",
                      "from huggingface_hub import snapshot_download; snapshot_download('mlx-community/whisper-large-v3-turbo')"]))
    for name, cmd in steps:
        print(f"… {name}", flush=True)
        code, out = run(cmd, timeout=3600)
        print(f"{OK if code == 0 else BAD} {name}" + ("" if code == 0 else f"\n{out[-800:]}"), flush=True)


def main():
    check()
    print("vlog-studio 安装自检\n")
    for mark, item, detail, fix in rows:
        print(f"{mark} {item}：{detail}")
        if fix and mark != OK:
            print(f"     怎么修：{fix}")
    print("\n结论：" + ("有必须先修的问题（❌），修好后再运行一次。" if must_fix else "可以开始用了。"))
    if "--prefetch" in sys.argv and not must_fix:
        prefetch()
    sys.exit(1 if must_fix else 0)


if __name__ == "__main__":
    main()
