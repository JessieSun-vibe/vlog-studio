# 一键安装：把下面这段话复制给你的 Claude Code 或 Codex

（也可以只把仓库链接发给 AI，说「帮我装上这个」；它只装了一半时，再把这段完整的话发给它。）

```text
请帮我安装并配置剪 vlog 的 skill「vlog-studio」：https://github.com/JessieSun-vibe/vlog-studio
按下面步骤做，每完成一步用一句话告诉我结果；需要装软件、下载大文件或者改设置之前，先告诉我要做什么、多大，等我同意。
路径里有中文或空格时，命令里要加引号。

0. 先看是不是已经装过：Claude Code 运行 `claude plugin list`（找不到 claude 命令就看 ~/.claude/plugins 里有没有 vlog-studio），Codex 看 ~/.codex/skills/vlog-studio 是否存在；再看 ~/.claude/vlog-studio/style.json 是否存在。
   已经装过就告诉我，改成问我要不要更新（Claude Code：`claude plugin marketplace update vlog-studio && claude plugin update vlog-studio@vlog-studio`；Codex：在 ~/vlog-studio 里 `git pull`），然后直接跳到第 3 步自检。

1. 基础工具（全新的 Mac 先做这步）：
   - 运行 `which brew || ls /opt/homebrew/bin/brew`。
   - 完全没有 Homebrew：告诉我需要装 Homebrew（它会顺带装好 Xcode 命令行工具，约 1–2GB，要输入电脑密码）。把这条命令发给我，让我自己在「终端」App 里运行，不要替我运行：
     /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
     等我说装好了，再运行 `echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile` 和 `eval "$(/opt/homebrew/bin/brew shellenv)"`，让 brew 在你的终端里也能用。
   - 有 /opt/homebrew/bin/brew 但 `which brew` 找不到：只运行上面那两行 eval。
   - 然后告诉我要装 ffmpeg 和 uv（几百 MB），我同意后运行 `brew install ffmpeg uv`。

2. 安装 skill：
   - Claude Code：运行 `claude plugin marketplace add JessieSun-vibe/vlog-studio` 和 `claude plugin install vlog-studio@vlog-studio`。如果终端里没有 claude 命令（比如在桌面 App 里），请我在对话框里依次输入 `/plugin marketplace add JessieSun-vibe/vlog-studio` 和 `/plugin install vlog-studio@vlog-studio`；输入后用下面的 ls 命令确认装上了，没装上就请我把报错发给你。
   - Codex：`git clone https://github.com/JessieSun-vibe/vlog-studio.git ~/vlog-studio`，`mkdir -p ~/.codex/skills`，再 `ln -s ~/vlog-studio/plugin/skills/vlog-studio ~/.codex/skills/vlog-studio`。
   - 其他支持 SKILL.md 的工具：把 ~/vlog-studio/plugin/skills/vlog-studio 链接或复制到它们读取 skills 的文件夹（不确定是哪个就问我）。
   然后确定「skill 文件夹」（后面的命令都用它）：
   - Claude Code：`ls -td ~/.claude/plugins/cache/vlog-studio/vlog-studio/*/skills/vlog-studio | head -1`（取最新安装的那个版本；没有结果再用 `find ~/.claude/plugins -path "*skills/vlog-studio/scripts/doctor.py"` 找）。
   - Codex：~/vlog-studio/plugin/skills/vlog-studio。

3. 自检：`python3 "<skill 文件夹>/scripts/doctor.py"`（只检查，不改东西）。有 ❌ 就告诉我缺什么，我同意后按它给的「怎么修」做，再自检，直到没有 ❌。

4. 提前下载：告诉我约 2GB（语音识别模型约 1.5GB + Python 依赖约 0.5GB + 一个很小的人脸模型，网速慢要等一阵），我同意后运行 `python3 "<skill 文件夹>/scripts/doctor.py" --prefetch`。我不同意就跳过，第一次剪片时会自动下载。

5. 风格档案 ~/.claude/vlog-studio/style.json：
   - 已经有了：把里面的角标文字、字幕顺序、素材库位置告诉我，问我要不要改，不要直接覆盖。
   - 还没有：先 `mkdir -p ~/.claude/vlog-studio`，再复制 <skill 文件夹>/styles/template.json 过去，只问我两件事并填进去：
     ① 左上角角标写什么 → 填 brand.text（不要角标就填空字符串）；
     ② 字幕中文在上还是英文在上 → 填 subtitles.order：中文在上是 "cn_en"，英文在上是 "en_cn"。
     字体、音效、素材库这些先不用填，下一步建素材库时会自动填好。

6. 素材库：问我放在哪个文件夹（建议 ~/vlog素材库），告诉我约 45MB（从 Google 官方下载的字体和贴图 + skill 自带的音效），我同意后运行：
   `python3 "<skill 文件夹>/scripts/setup_library.py" "<素材库文件夹>" --update-style ~/.claude/vlog-studio/style.json`
   如果最后提示有几个下载失败，再运行一次同样的命令就会续传。完成后打开素材库里的「素材预览.html」给我看（装了 Chrome 就用 Chrome，没有就用默认浏览器；Safari 里动态贴图不会动，这是正常的）。

7. 最后告诉我：上面这些在当前会话里就能做完；真正剪片时请新开一个会话（让 skill 自动生效），说「用 vlog-studio 帮我剪 <素材文件夹>」就能开始；剪片时它会在画幅、口播稿、分镜确认这几步停下来问我。
```

## English version

```text
Please install and set up the vlog editing skill "vlog-studio": https://github.com/JessieSun-vibe/vlog-studio
Do the steps below and tell me the result of each in one sentence. Before installing software, downloading large files or changing settings, tell me what and how big, and wait for my OK. Quote paths that contain spaces or non-ASCII characters.

0. Already installed? Claude Code: `claude plugin list` (or look for vlog-studio under ~/.claude/plugins if there's no claude command); Codex: does ~/.codex/skills/vlog-studio exist? Also check ~/.claude/vlog-studio/style.json. If installed, tell me and offer an update instead (Claude Code: `claude plugin marketplace update vlog-studio && claude plugin update vlog-studio@vlog-studio`; Codex: `git pull` in ~/vlog-studio), then go to step 3.
1. Base tools (do this first on a new Mac): run `which brew || ls /opt/homebrew/bin/brew`.
   - No Homebrew at all: tell me it's needed (it also installs Xcode Command Line Tools, ~1–2GB, asks for my password). Give me this command to run myself in Terminal; don't run it for me:
     /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
     When I say it's done, run `echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile` and `eval "$(/opt/homebrew/bin/brew shellenv)"`.
   - /opt/homebrew/bin/brew exists but `which brew` fails: just run those two eval lines.
   - Then tell me ffmpeg and uv are needed (a few hundred MB); after my OK run `brew install ffmpeg uv`.
2. Install the skill:
   - Claude Code: `claude plugin marketplace add JessieSun-vibe/vlog-studio` and `claude plugin install vlog-studio@vlog-studio`. If there's no claude command (e.g. in the desktop app), ask me to type `/plugin marketplace add JessieSun-vibe/vlog-studio` and `/plugin install vlog-studio@vlog-studio` in the chat box.
   - Codex: `git clone https://github.com/JessieSun-vibe/vlog-studio.git ~/vlog-studio`, `mkdir -p ~/.codex/skills`, `ln -s ~/vlog-studio/plugin/skills/vlog-studio ~/.codex/skills/vlog-studio`.
   - Other SKILL.md agents: link or copy ~/vlog-studio/plugin/skills/vlog-studio into their skills folder (ask me if unsure).
   Find the "skill folder": Claude Code: `ls -td ~/.claude/plugins/cache/vlog-studio/vlog-studio/*/skills/vlog-studio | head -1` (newest installed version; if empty, `find ~/.claude/plugins -path "*skills/vlog-studio/scripts/doctor.py"`); Codex: ~/vlog-studio/plugin/skills/vlog-studio.
3. Self-check: `python3 "<skill folder>/scripts/doctor.py"` (read-only). For every ❌ tell me what's missing and, after my OK, apply its fix; re-run until there's none.
4. Pre-download: ~2GB (speech model ~1.5GB + Python packages ~0.5GB + a small face model); after my OK run `python3 "<skill folder>/scripts/doctor.py" --prefetch`. If I say no, skip; it downloads on first use.
5. Style profile ~/.claude/vlog-studio/style.json:
   - Exists: tell me its badge text, subtitle order and library location; ask before changing. Don't overwrite.
   - Missing: `mkdir -p ~/.claude/vlog-studio`, copy <skill folder>/styles/template.json there and ask me only two things: (1) corner badge text → brand.text (empty string for none); (2) Chinese or English line on top → subtitles.order "cn_en" (Chinese on top) or "en_cn" (English on top). Leave fonts / SFX / library fields; the next step fills them.
6. Asset library: ask where to put it (suggest ~/vlog-assets), tell me ~45MB (fonts and stickers from Google + bundled SFX); after my OK run
   `python3 "<skill folder>/scripts/setup_library.py" "<library folder>" --update-style ~/.claude/vlog-studio/style.json`
   If it reports some failed downloads, run the same command again to resume. Then open its 素材预览.html (Chrome if installed, otherwise the default browser; animated stickers don't move in Safari, which is expected).
7. Finally tell me: everything above runs in this session; to actually edit, start a new session (so the skill loads) and say "use vlog-studio to edit <footage folder>"; it will stop to ask me about aspect ratio, script and storyboard approval.
```
