#!/usr/bin/env python3
"""人脸跟踪：每隔一小段时间找一次画面里的人脸，输出平滑后的位置，给「跟着脸走的贴图」和「大头特效」用。

  uv run --with opencv-python python face_track.py <视频> <输出.json> [--start 0] [--end 20] [--fps 10]

输出 {"width","height","samples":[{"t":秒,"faces":[{"cx","cy","w","h"}...]}...]}，坐标是 0–1 的比例，
人脸按从左到右排序（多人时 faces[0] 是画面左边的人）。用 OpenCV 自带的 YuNet 人脸检测（戴墨镜、帽子也能认），
没有模型时退回 Haar。
"""
import argparse, json, os, urllib.request

YUNET_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
CACHE = os.path.expanduser("~/.cache/vlog-studio/face_detection_yunet_2023mar.onnx")


def detector(w, h):
    import cv2
    try:
        if not os.path.exists(CACHE):
            os.makedirs(os.path.dirname(CACHE), exist_ok=True)
            urllib.request.urlretrieve(YUNET_URL, CACHE)
        det = cv2.FaceDetectorYN.create(CACHE, "", (w, h), 0.6, 0.3, 50)
        def run(img):
            _, faces = det.detect(img)
            return [] if faces is None else [tuple(float(v) for v in f[:4]) for f in faces]
        return run, "yunet"
    except Exception:
        casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        def run(img):
            g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            return [tuple(map(float, f)) for f in casc.detectMultiScale(g, 1.1, 5, minSize=(40, 40))]
        return run, "haar"


def smooth(samples, k=2):
    """对每个人（按左右顺序）的位置做简单滑动平均，去掉抖动。"""
    n = max((len(s["faces"]) for s in samples), default=0)
    for i in range(n):
        for key in ("cx", "cy", "w", "h"):
            vals = [s["faces"][i][key] if len(s["faces"]) > i else None for s in samples]
            for j, s in enumerate(samples):
                if len(s["faces"]) > i:
                    win = [v for v in vals[max(0, j - k):j + k + 1] if v is not None]
                    s["faces"][i][key] = round(sum(win) / len(win), 4)
    return samples


def main():
    import cv2
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("out")
    ap.add_argument("--start", type=float, default=0); ap.add_argument("--end", type=float); ap.add_argument("--fps", type=float, default=10)
    a = ap.parse_args()
    cap = cv2.VideoCapture(a.video)
    W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    dur = cap.get(cv2.CAP_PROP_FRAME_COUNT) / (cap.get(cv2.CAP_PROP_FPS) or 30)
    end = a.end or dur
    scale = 960 / W; sw, sh = 960, int(H * scale)
    run, kind = detector(sw, sh)
    samples, t = [], a.start
    while t <= end:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, img = cap.read()
        if not ok:
            break
        img = cv2.resize(img, (sw, sh))
        faces = sorted(run(img), key=lambda f: f[0])
        samples.append({"t": round(t, 3), "faces": [{"cx": (x + w / 2) / sw, "cy": (y + h / 2) / sh, "w": w / sw, "h": h / sh}
                                                     for x, y, w, h in faces]})
        t += 1 / a.fps
    samples = smooth(samples)
    json.dump({"video": os.path.abspath(a.video), "width": W, "height": H, "detector": kind, "samples": samples}, open(a.out, "w"), indent=1)
    counts = [len(s["faces"]) for s in samples]
    print(f"{kind}：{len(samples)} 个采样点，人脸数 {min(counts) if counts else 0}–{max(counts) if counts else 0}，"
          f"有脸的采样占 {sum(1 for c in counts if c) / max(1, len(counts)):.0%}")


if __name__ == "__main__":
    main()
