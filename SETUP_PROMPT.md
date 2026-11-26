# 一键安装：把下面这段话复制给你的 Claude Code 或 Codex

```text
请帮我安装并配置剪 vlog 的 skill「vlog-studio」：https://github.com/JessieSun-vibe/vlog-studio
按下面步骤做，每完成一步用一句话告诉我结果；需要装软件、下载大文件或者改设置之前，先告诉我要做什么、多大，等我同意。

1. 安装 skill：
   - 如果你是 Claude Code：运行 `claude plugin marketplace add JessieSun-vibe/vlog-studio` 和 `claude plugin install vlog-studio@vlog-studio`。
   - 如果你是 Codex 或其他支持 SKILL.md 的工具：把仓库 git clone 到 ~/vlog-studio，再把 ~/vlog-studio/plugin/skills/vlog-studio 链接到你的 skills 文件夹（Codex 是 ~/.codex/skills/vlog-studio）。
2. 运行 skill 里的自检脚本：`python3 <skill 文件夹>/scripts/doctor.py`。
   有 ❌ 的项，按它给的「怎么修」命令帮我装好（比如 `brew install ffmpeg uv`），装完再自检一次，直到没有 ❌。
3. 提前下载模型：告诉我大约要下载 2GB（语音识别模型约 1.5GB），我同意后运行 `python3 <skill 文件夹>/scripts/doctor.py --prefetch`。
4. 问我 3 个问题，用它们建立风格档案 ~/.claude/vlog-studio/style.json（以 <skill 文件夹>/styles/template.json 为模板）：
   ① 视频左上角的角标写什么（比如「Bali vlog」，也可以不要）；
   ② 字幕中文在上还是英文在上；
   ③ 素材库放在哪个文件夹（建议 ~/vlog素材库）。
5. 我同意后，建立素材库（约 45MB）：`python3 <skill 文件夹>/scripts/setup_library.py <素材库文件夹> --update-style ~/.claude/vlog-studio/style.json`，完成后用 Chrome 打开素材库里的「素材预览.html」给我看。
6. 最后告诉我：新开一个会话，说「用 vlog-studio 帮我剪 <素材文件夹>」就能开始，以及剪片时它会在哪几步停下来问我（画幅、口播稿、分镜确认）。
```

## English version

```text
Please install and set up the vlog editing skill "vlog-studio": https://github.com/JessieSun-vibe/vlog-studio
Do the steps below and tell me the result of each in one sentence. Before installing software, downloading large files or changing settings, tell me what and how big, and wait for my OK.

1. Install the skill:
   - Claude Code: run `claude plugin marketplace add JessieSun-vibe/vlog-studio` and `claude plugin install vlog-studio@vlog-studio`.
   - Codex or another SKILL.md agent: git clone the repo to ~/vlog-studio and link ~/vlog-studio/plugin/skills/vlog-studio into your skills folder (for Codex: ~/.codex/skills/vlog-studio).
2. Run the self-check: `python3 <skill folder>/scripts/doctor.py`. Fix every ❌ with the command it suggests (e.g. `brew install ffmpeg uv`) and re-run until there is none.
3. Pre-download models: tell me it's about 2GB (speech model ~1.5GB); after I agree, run `python3 <skill folder>/scripts/doctor.py --prefetch`.
4. Ask me 3 questions and create my style profile ~/.claude/vlog-studio/style.json from <skill folder>/styles/template.json: (1) corner badge text (or none); (2) Chinese or English subtitle line on top; (3) where to put my asset library (suggest ~/vlog-assets).
5. After I agree, build the asset library (~45MB): `python3 <skill folder>/scripts/setup_library.py <library folder> --update-style ~/.claude/vlog-studio/style.json`, then open its 素材预览.html in Chrome for me.
6. Finally tell me: start a new session and say "use vlog-studio to edit <footage folder>", and where it will stop to ask me (aspect ratio, script, storyboard approval).
```
