# 风格档案（style.json）

位置：`~/.claude/vlog-studio/style.json`（每个人自己的，不随 skill 分享）。第一次用时复制 `template.json` 过去再改。

| 字段 | 作用 |
|---|---|
| `name` | 风格名字 |
| `spec_doc` | 用户自己的风格规范文档路径（有就先读，里面确认过的规则优先） |
| `size` / `fps` | 默认画幅和帧率；实际画幅跟拍摄方向走，改之前先问 |
| `fonts.subtitle` | 字幕字体（中文要能显示）；`fonts.fun` 花字和章节标签用的圆体/手写体；`fonts.brand` 角标字体。找不到会退回系统字体 |
| `brand` | 左上角固定角标：文字、字号、位置、颜色。每支片子可在时间线里用 `"brand"` 覆盖 |
| `chapter_tag` | 章节标签（定位图钉 + 彩色字），位置在角标下面 |
| `fx` | 花字：字号、填充色、描边色、描边宽、倾斜角度、垂直位置 |
| `subtitles` | `order`：`cn_en`（中文在上）或 `en_cn`；字号、位置、行距、底条透明度、单行最大宽度（超了按标点拆） |
| `sfx` | 音效名 → 文件。`chapter`（换章节）、`page`（翻页）、`photo`（快门）、`pop`（花字弹出，留空则自动合成），可以加任意名字（ding、whoosh…），时间线里按名字用 |
| `library` / `asset_catalog` | 素材库文件夹和素材清单（每个贴图/音效的含义、场景、授权），剪片时按清单挑素材 |
| `stickers_dir` | 自己的贴图库文件夹（可用 `scripts/fetch_stickers.py` 往里加 Noto 动态表情） |
| `bg_under_speech` | 有人说话时原视频环境声的音量（0.12 ≈ 12%） |
| `speech_lufs` / `music_lufs` / `master_lufs` | 人声、现场音乐、整片的目标响度 |
| `default_speed` | 用户习惯的整片变速（如 1.2），成片后用 `speedup.py` |
