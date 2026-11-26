#!/usr/bin/env python3
"""下载 Google Noto 动态表情贴图（CC BY 4.0，带透明背景的 webm），并记下来源、授权、校验码和状态。

  python3 fetch_stickers.py <目标文件夹> dog tropical-drink heart-eyes ...   # 名字见 --list
  python3 fetch_stickers.py --list                                         # 列出全部可用名字

下载前先问用户（会从 GitHub 下载文件）。发布视频时附上 CREDITS.md 里的署名。
来源：https://github.com/remotion-dev/animated-emoji （预渲染自 https://googlefonts.github.io/noto-emoji-animation/）
"""
import hashlib, json, os, subprocess, sys

RAW = "https://raw.githubusercontent.com/remotion-dev/animated-emoji/main/public/{}-1x.webm"


def list_names():
    r = subprocess.run(["gh", "api", "repos/remotion-dev/animated-emoji/git/trees/main?recursive=1", "--jq", ".tree[].path"],
                       capture_output=True, text=True)
    if r.returncode:
        r = subprocess.run(["curl", "-sL", "https://api.github.com/repos/remotion-dev/animated-emoji/git/trees/main?recursive=1"],
                           capture_output=True, text=True)
        paths = [t["path"] for t in json.loads(r.stdout).get("tree", [])]
    else:
        paths = r.stdout.split()
    print(" ".join(sorted(p[7:-8] for p in paths if p.startswith("public/") and p.endswith("-1x.webm"))))


def main():
    if "--list" in sys.argv:
        return list_names()
    dest, names = sys.argv[1], sys.argv[2:]
    os.makedirs(dest, exist_ok=True)
    rec_path = os.path.join(dest, "来源与状态.json")
    recs = json.load(open(rec_path, encoding="utf-8")) if os.path.exists(rec_path) else []
    have = {r["name"] for r in recs}
    for n in names:
        p = os.path.join(dest, f"{n}.webm")
        r = subprocess.run(["curl", "-sSfL", "--max-time", "90", "-o", p, RAW.format(n)])
        if r.returncode:
            print(f"失败：{n}"); continue
        if n not in have:
            recs.append({"name": n, "source": RAW.format(n), "creator": "Google Fonts Animated Emoji", "license": "CC BY 4.0",
                         "sha256": hashlib.sha256(open(p, "rb").read()).hexdigest(), "status": "downloaded_not_yet_user_approved",
                         "path": p})
        print(f"OK {n} {os.path.getsize(p) // 1024}KB")
    json.dump(recs, open(rec_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    cred = os.path.join(dest, "CREDITS.md")
    if not os.path.exists(cred):
        open(cred, "w", encoding="utf-8").write("# 贴图署名\n\n动态表情贴图：Google Noto Emoji Animation（CC BY 4.0）\n"
                              "https://googlefonts.github.io/noto-emoji-animation/ · 文件来自 https://github.com/remotion-dev/animated-emoji\n")


if __name__ == "__main__":
    main()
