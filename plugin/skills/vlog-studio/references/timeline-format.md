# 时间线 JSON 格式（render.py 的输入）

```json
{
  "output": "/path/项目-小样-v1.mp4",
  "voiceover": "/path/口播-剪辑版.wav",
  "brand": "Bali vlog",
  "bgm": {"file": "/path/bgm.mp3", "volume": 0.15},
  "pieces": [
    {
      "chapter": "入住", "tag": "入住",
      "audio": {"type": "vo", "from": 13.18, "to": 21.12},
      "video": {"src": "/素材/room.mp4", "start": 8.9, "speed": 0.65},
      "subs": [[0.1, 2.3, "海景双人房，住了两晚", "A sea-view double, two nights"]],
      "fx": {"text": "两晚 800 元！", "at": 4.0},
      "stickers": [{"file": "/贴图/money-face.webm", "x": 1480, "y": 290, "size": 200, "at": 4.0}],
      "sfx": [{"name": "chapter", "at": 0.03}]
    }
  ]
}
```

- `audio.type`：`vo`（口播文件 from→to，时长由它决定）、`clip`（视频自己的声音：现场原声 / 对镜口播，需要 `duration`）、`music`（现场音乐）、`ambient`（环境声，`bg_volume`）、`none`。
- `video`：`{"src","start","speed"}`；照片 `{"photo","zoom","cx","cy"}`；快剪 `{"montage": [[src, t], ...]}`；可加 `"pip": 照片路径`（右上角小窗）。
- `subs` 时间是片段内相对秒数，用 `timeline_tools.cue_times()` 算；太长的句子渲染时会自动按标点拆开。
- `sfx.name` 对应风格档案里的 `chapter / page / photo / pop`，也可写 `"file"`。有 `fx` 时会自动加「啵」。
- 贴图支持带透明的 `.webm`（播一遍后消失）、`.png`、`.svg`（弹出后停留）。加 `"follow"` 就跟着脸走（循环播放）：`{"track": faces.json, "who": 0, "dx": 0.8, "dy": -0.6, "size": 0.7, "pop": true, "bob_hz": 0.8}`，dx/dy/size 以脸宽为单位；`"until"` 可以让它提前消失。
- `fx` 可以加 `"y"` 单独调高度；`card`：`{"title","sub","icons":[svg/png],"x","y","at","rotate","bg","color"}` 信息卡。
- 一句话跨了剪辑点：两段都放同一条字幕，SRT 里会自动合成一条。

## 每个项目写一个 build_timeline.py

```python
import json, sys; sys.path.insert(0, "<skill>/scripts")
from timeline_tools import Transcript, shared_cuts, cue_times
vo = Transcript("work/transcripts/口播-剪辑版.json")
groups = [[1, 2], [3, 4, 5, 6]]                    # 每个口播片段用到的段落号
cuts = shared_cuts(vo, groups)                      # 相邻片段共用切点
pieces = [{"chapter": "入住", "tag": "入住",
           "audio": {"type": "vo", "from": cuts[0][0], "to": cuts[0][1]},
           "video": {"src": "...", "start": 0.0, "speed": .85},
           "subs": cue_times(vo, [("这是我们住的第二家酒店", "Our second hotel", [1])], cuts[0][0])}]
json.dump({"output": "...", "voiceover": "...", "pieces": pieces}, open("timeline.json", "w"), ensure_ascii=False, indent=1)
```
现场原声片段：`{"audio": {"type": "clip"}, "video": {"src": 原视频, "start": 说话开始-0.25}, "duration": 说话长度+0.6}`，字幕时间从该视频的转写算。
