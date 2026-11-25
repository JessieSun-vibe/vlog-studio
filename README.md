# vlog-studio

**把手机 / 相机拍的生活素材，剪成可以直接发小红书、B 站、抖音的 vlog。**
交给你的 AI 编程助手（Claude Code、Codex 等），说一句「帮我把这些素材剪成 vlog」，它会看素材、转写语音、写口播稿、出分镜给你确认，然后剪出带中英双语字幕、章节标签、花字、动态贴图和音效的成片。

[English](#english) · [安装](#安装) · [怎么用](#怎么用)

![成片示例：海岛酒店 vlog](docs/images/cover.jpg)

<sub>示例画面来自一支海岛酒店 room tour：花字「不潮！」「每顿必点！」「零踩雷」、动态表情贴图、双语字幕、左上角角标和章节标签都是这个 skill 自动做的。</sub>

## 能做什么

| | |
|---|---|
| **三种视频** | 旁白口播 + 画面（先拍后录）、对镜头口播（自拍 / 合照说话）、纯画面 vlog |
| **人声清理** | 本地转写，找出停顿、说了两遍的句子、说错的词，剪掉后再转写一遍核对没切掉字 |
| **现场原声** | 拍摄时随口说的「哇好用心」「好喜欢这个床」会被找出来，和后期口播混剪，更有活人感 |
| **双语字幕** | 中文在上英文在下（可改），长句按标点自动拆开，同时导出 SRT 可导入剪映 |
| **包装** | 左上角固定角标、章节标签滑入、花字弹出、信息卡（日期 · 地点 · 价格）、照片小窗、快剪开场 |
| **动态贴图** | Google Noto 动态表情（带透明），可以**跟着人脸走**（说到「婚礼」时两人脸旁各飘一颗爱心） |
| **音效** | 换章节、拍照、花字弹出等时刻自动加音效，人声说话时环境声自动压低，整片统一响度 |
| **先出分镜** | 渲染前一定先出分镜页：每段一张样张，贴图、花字、信息卡都画在真实位置，确认后才生成视频 |
| **变速** | 整片 1.2 倍速等，人声音调不变，字幕同步 |

## 工作流程

```
看素材 → 转写人声 → 写口播稿 / 选现场原声 → 剪停顿和重复 → 搭时间线
      → 出分镜，等你确认 → 渲染 → 重新转写成片自查 → 交付 MP4 + SRT
```

每一步需要你决定的事（画幅、口播稿、保留哪些原声、分镜）都会停下来问你；字幕只写你说过的话，不替你编感受。

## 安装

### 电脑要求
- **Mac（Apple 芯片，M1 及以后）**：全部功能可用（本地语音转写用 mlx-whisper）。
- Windows / Intel Mac：剪辑和渲染部分可以跑，本地转写暂不支持（欢迎 PR）。
- 需要先装好：[ffmpeg](https://ffmpeg.org/)（带 libvpx）、Python 3、[uv](https://docs.astral.sh/uv/)。其余依赖第一次使用时自动安装。

```bash
brew install ffmpeg uv
```

### Claude Code（推荐）

```bash
claude plugin marketplace add JessieSun-vibe/vlog-studio
```
```bash
claude plugin install vlog-studio@vlog-studio
```

更新：
```bash
claude plugin marketplace update vlog-studio && claude plugin update vlog-studio@vlog-studio
```

### Codex 或其他支持 SKILL.md 的工具

```bash
git clone https://github.com/JessieSun-vibe/vlog-studio.git ~/vlog-studio
```
```bash
ln -s ~/vlog-studio/plugin/skills/vlog-studio ~/.codex/skills/vlog-studio
```

其他工具把 `plugin/skills/vlog-studio` 放进它们的 skills 文件夹即可。更新时在 `~/vlog-studio` 里 `git pull`。

## 怎么用

把一支片子的素材放进一个文件夹（建议分 `原始素材/` 和 `生成素材/`），然后对你的 AI 助手说：

> 用 vlog-studio 帮我剪这个视频，素材在「桌面/海岛酒店」，是旁白口播，酒店叫 XXX，两晚 800，我打 9.5 分。

**第一次使用**时，它会问你几个风格偏好（角标文字、字幕中英顺序、有没有自己的字体 / 音效 / 贴图），存成你自己的风格档案 `~/.claude/vlog-studio/style.json`，以后每支片子都沿用。

### 素材库（贴图、音效、字体）
仓库里不带素材。建议建一个自己的素材库，在风格档案里指向它：
- **动态贴图**：`scripts/fetch_stickers.py` 可下载 Google Noto 动态表情（CC BY 4.0，发布时注明出处）。
- **字体**：推荐 Google Fonts 上可商用的中文字体，如站酷快乐体（花字）、龙藏体（手写感）。
- **音效**：用自己有授权的音效；不要直接从别人的成片里截取。

## 文件结构

```
plugin/skills/vlog-studio/
├── SKILL.md                 流程说明（AI 读这个）
├── scripts/                 看素材、转写、清理人声、人脸跟踪、分镜、渲染、变速、下载贴图
├── references/              时间线格式、三种视频类型、踩过的坑
└── styles/                  风格档案模板和字段说明
```

## 致谢

动态表情：[Google Noto Emoji Animation](https://googlefonts.github.io/noto-emoji-animation/)（CC BY 4.0）· 语音转写：[mlx-whisper](https://github.com/ml-explore/mlx-examples) · 人脸检测：[OpenCV YuNet](https://github.com/opencv/opencv_zoo)

## License

代码和文档：MIT。贴图、字体等第三方素材按各自的授权使用。

---

## English

**vlog-studio** is an agent skill that turns your phone / camera footage into a share-ready lifestyle vlog (Xiaohongshu, Bilibili, TikTok style). Give your coding agent (Claude Code, Codex, …) a folder of clips and say "edit this into a vlog". It will:

- inspect the footage and transcribe every voice (on-device, mlx-whisper on Apple Silicon);
- write or clean up the voiceover: trim pauses, drop repeated takes and misspoken words, and re-transcribe to verify nothing was clipped;
- mix in the natural reactions you said while filming;
- build a timeline where picture follows the audio, with bilingual subtitles (exported as SRT), a corner badge, chapter tags, pop-up captions, info cards, picture-in-picture, animated Noto emoji stickers (optionally **tracking faces**), and event-based sound effects;
- **show you a storyboard before rendering** (one still per segment with every sticker / caption / card drawn at its real position), and only render after you approve;
- render MP4 + SRT at −16 LUFS, optionally speed up (pitch preserved), and self-check the result.

Three video types are supported: voiceover + B-roll, talking-head (to camera), and visuals-only.

**Requirements:** macOS on Apple Silicon for the full pipeline; `ffmpeg` (with libvpx), Python 3 and `uv`.

**Install (Claude Code):**
```bash
claude plugin marketplace add JessieSun-vibe/vlog-studio
```
```bash
claude plugin install vlog-studio@vlog-studio
```

**Install (Codex / other SKILL.md agents):** clone this repo and link `plugin/skills/vlog-studio` into your agent's skills folder (e.g. `~/.codex/skills/`).

On first use the agent asks for your style preferences (badge text, subtitle order, your own fonts / stickers / SFX) and saves them to `~/.claude/vlog-studio/style.json`. No stickers, fonts or sounds are bundled; `scripts/fetch_stickers.py` downloads Google Noto animated emoji (CC BY 4.0 — credit them when you publish).

License: MIT for code and docs; third-party assets keep their own licenses.
