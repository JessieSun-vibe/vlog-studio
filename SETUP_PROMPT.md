# 一键安装：把下面这段话复制给你的 Claude Code 或 Codex

（也可以只把仓库链接发给 AI，说「帮我装上这个」；它只装了一半时，再把这段完整的话发给它。）

```text
请帮我安装并配置剪 vlog 的 skill「vlog-studio」：https://github.com/JessieSun-vibe/vlog-studio
按下面步骤做，每完成一步用一句话告诉我结果；需要装软件、下载大文件或者改设置之前，先告诉我要做什么、多大，等我同意。

0. 先看是不是已经装过：Claude Code 运行 `claude plugin list`，Codex 看 ~/.codex/skills/vlog-studio 是否存在；再看 ~/.claude/vlog-studio/style.json 是否存在。
   已经装过就告诉我，改成问我要不要更新（Claude Code：`claude plugin marketplace update vlog-studio && claude plugin update vlog-studio@vlog-studio`；Codex：在 ~/vlog-studio 里 `git pull`），然后直接跳到第 2 步自检。
1. 安装 skill：
   - Claude Code：运行 `claude plugin marketplace add JessieSun-vibe/vlog-studio` 和 `claude plugin install vlog-studio@vlog-studio`。
   - Codex：`git clone https://github.com/JessieSun-vibe/vlog-studio.git ~/vlog-studio`，`mkdir -p ~/.codex/skills`，再 `ln -s ~/vlog-studio/plugin/skills/vlog-studio ~/.codex/skills/vlog-studio`。
   - 其他支持 SKILL.md 的工具：把 ~/vlog-studio/plugin/skills/vlog-studio 链接或复制到它们读取 skills 的文件夹（不确定是哪个就问我）。
   然后确定「skill 文件夹」（后面的命令都用它）：
   - Claude Code：运行 `find ~/.claude/plugins -path "*skills/vlog-studio/scripts/doctor.py" | head -1`，去掉结尾的 /scripts/doctor.py 就是 skill 文件夹。
   - Codex：~/vlog-studio/plugin/skills/vlog-studio。
2. 运行自检：`python3 <skill 文件夹>/scripts/doctor.py`（只检查，不改东西）。
   有 ❌ 的项，告诉我缺什么，我同意后按它给的「怎么修」命令装好（比如 `brew install ffmpeg uv`），装完再自检一次，直到没有 ❌。
   如果连 Homebrew 都没有：把它给的 Homebrew 安装命令发给我，让我自己在终端运行（需要输入电脑密码），不要替我运行。
3. 提前下载：告诉我大约 2GB（语音识别模型约 1.5GB + Python 依赖约 0.5GB），我同意后运行 `python3 <skill 文件夹>/scripts/doctor.py --prefetch`。我不同意就跳过，第一次剪片时会自动下载。
4. 风格档案 ~/.claude/vlog-studio/style.json：
   - 已经有了：把里面的角标文字、字幕顺序、素材库位置告诉我，问我要不要改，不要直接覆盖。
   - 还没有：问我 3 个问题，以 <skill 文件夹>/styles/template.json 为模板建立：① 视频左上角的角标写什么（比如「Bali vlog」，也可以不要）；② 字幕中文在上还是英文在上；③ 素材库放在哪个文件夹（建议 ~/vlog素材库）。
5. 素材库：如果风格档案里还没有素材库，告诉我大约 45MB（从 Google 官方下载的字体和贴图 + skill 自带的音效），我同意后运行 `python3 <skill 文件夹>/scripts/setup_library.py <素材库文件夹> --update-style ~/.claude/vlog-studio/style.json`。
   完成后打开素材库里的「素材预览.html」给我看（装了 Chrome 就用 Chrome，没有就用默认浏览器）。
6. 最后告诉我：上面这些在当前会话里就能做完；真正剪片时请新开一个会话（让 skill 自动生效），说「用 vlog-studio 帮我剪 <素材文件夹>」就能开始；剪片时它会在画幅、口播稿、分镜确认这几步停下来问我。
```

## English version

```text
Please install and set up the vlog editing skill "vlog-studio": https://github.com/JessieSun-vibe/vlog-studio
Do the steps below and tell me the result of each in one sentence. Before installing software, downloading large files or changing settings, tell me what and how big, and wait for my OK.

0. Check whether it's already installed: Claude Code: `claude plugin list`; Codex: does ~/.codex/skills/vlog-studio exist? Also check ~/.claude/vlog-studio/style.json.
   If it's installed, tell me and offer an update instead (Claude Code: `claude plugin marketplace update vlog-studio && claude plugin update vlog-studio@vlog-studio`; Codex: `git pull` in ~/vlog-studio), then go to step 2.
1. Install the skill:
   - Claude Code: `claude plugin marketplace add JessieSun-vibe/vlog-studio` and `claude plugin install vlog-studio@vlog-studio`.
   - Codex: `git clone https://github.com/JessieSun-vibe/vlog-studio.git ~/vlog-studio`, `mkdir -p ~/.codex/skills`, `ln -s ~/vlog-studio/plugin/skills/vlog-studio ~/.codex/skills/vlog-studio`.
   - Other SKILL.md agents: link or copy ~/vlog-studio/plugin/skills/vlog-studio into the folder they load skills from (ask me if unsure).
   Then find the "skill folder" used below:
   - Claude Code: `find ~/.claude/plugins -path "*skills/vlog-studio/scripts/doctor.py" | head -1`, minus the trailing /scripts/doctor.py.
   - Codex: ~/vlog-studio/plugin/skills/vlog-studio.
2. Self-check: `python3 <skill folder>/scripts/doctor.py` (read-only). For every ❌, tell me what's missing and, after my OK, run its suggested fix (e.g. `brew install ffmpeg uv`); re-run until there's none. If Homebrew itself is missing, give me its install command to run myself (it asks for my password); don't run it for me.
3. Pre-download: tell me it's about 2GB (speech model ~1.5GB + Python packages ~0.5GB); after my OK run `python3 <skill folder>/scripts/doctor.py --prefetch`. If I say no, skip it; it downloads on first use.
4. Style profile ~/.claude/vlog-studio/style.json:
   - If it exists: tell me its badge text, subtitle order and library location and ask whether to change anything. Don't overwrite it.
   - If not: ask me 3 questions and create it from <skill folder>/styles/template.json: (1) corner badge text (or none); (2) Chinese or English subtitle line on top; (3) where to put my asset library (suggest ~/vlog-assets).
5. Asset library: if the profile has none yet, tell me it's about 45MB (fonts and stickers from Google + bundled sound effects); after my OK run `python3 <skill folder>/scripts/setup_library.py <library folder> --update-style ~/.claude/vlog-studio/style.json`, then open its 素材预览.html (in Chrome if installed, otherwise the default browser).
6. Finally tell me: everything above runs in this session; to actually edit, start a new session (so the skill loads) and say "use vlog-studio to edit <footage folder>"; it will stop to ask me about aspect ratio, script and storyboard approval.
```
