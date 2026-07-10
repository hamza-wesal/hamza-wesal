#!/usr/bin/env python3
"""Convert face.webp into ASCII art: detect face, crop with padding,
remove background via GrabCut, map brightness to a character ramp,
and render both a .txt and a preview .png of the result.
"""
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SRC = "face.webp"
ASCII_TXT_OUT = "face_ascii.txt"
PREVIEW_PNG_OUT = "face_ascii_preview.png"
CASCADE_PATH = "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml"

WIDTH_CHARS = 46
VERTICAL_ASPECT = 0.5  # terminal chars are ~2x taller than wide

# Dense ramp, dark -> light. Index 0 = darkest/most "ink".
RAMP = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "


def load_bgr(path):
    im = Image.open(path).convert("RGB")
    arr = np.array(im)
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)


def detect_face(bgr):
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(CASCADE_PATH)
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
    if len(faces) == 0:
        raise RuntimeError("No face detected in " + SRC)
    # pick the largest detected face
    return max(faces, key=lambda f: f[2] * f[3])


def crop_with_padding(bgr, face_box):
    h, w = bgr.shape[:2]
    x, y, fw, fh = face_box
    # generous padding above for hair; minimal below so the crop ends at the
    # jawline instead of pulling in shoulders/background clutter (e.g. a
    # railing behind the subject), which read as noise at 46-char resolution
    pad_top = int(fh * 0.85)
    pad_bottom = int(fh * 0.02)
    pad_side = int(fw * 0.46)

    x0 = max(0, x - pad_side)
    x1 = min(w, x + fw + pad_side)
    y0 = max(0, y - pad_top)
    y1 = min(h, y + fh + pad_bottom)
    return bgr[y0:y1, x0:x1]


def remove_background_grabcut(bgr):
    h, w = bgr.shape[:2]
    mask = np.zeros((h, w), np.uint8)
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    # Seed rect: assume subject occupies the central majority of the crop.
    margin_x = int(w * 0.06)
    margin_y = int(h * 0.04)
    rect = (margin_x, margin_y, w - 2 * margin_x, h - 2 * margin_y)

    cv2.grabCut(bgr, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
    fg_mask = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype("uint8")

    # clean up small holes/noise
    kernel = np.ones((5, 5), np.uint8)
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)

    # keep only the largest connected component (drops disjoint background
    # fragments GrabCut occasionally keeps, e.g. railing bars near the body)
    num, labels, stats, _ = cv2.connectedComponentsWithStats(fg_mask, connectivity=8)
    if num > 2:
        largest = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
        fg_mask = np.where(labels == largest, 255, 0).astype("uint8")
    return fg_mask


def to_ascii(bgr, fg_mask, width_chars, vertical_aspect):
    h, w = bgr.shape[:2]
    height_chars = max(1, int(round((h / w) * width_chars * vertical_aspect)))

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    # bilateral filter smooths skin/hair/fabric texture noise while keeping
    # strong edges, so downsampling doesn't just average texture into static;
    # CLAHE then boosts local contrast so features aren't washed out
    smoothed = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)
    smoothed = cv2.bilateralFilter(smoothed, d=9, sigmaColor=75, sigmaSpace=75)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(smoothed)
    small_gray = cv2.resize(gray, (width_chars, height_chars), interpolation=cv2.INTER_AREA)
    # erode mask slightly before downsampling so stray edge pixels don't
    # survive as isolated foreground cells in the low-res grid
    eroded_mask = cv2.erode(fg_mask, np.ones((7, 7), np.uint8))
    small_mask = cv2.resize(eroded_mask, (width_chars, height_chars), interpolation=cv2.INTER_AREA)
    small_mask = np.where(small_mask > 127, 255, 0).astype("uint8")

    ramp_len = len(RAMP) - 1
    lines = []
    for row in range(height_chars):
        line_chars = []
        for col in range(width_chars):
            if small_mask[row, col] == 0:
                line_chars.append(" ")
                continue
            # dark image pixels -> dense/ink characters, bright pixels -> sparse
            # characters, so it reads correctly as dark-on-light text (GitHub's
            # default light theme, code-block rendering)
            brightness = small_gray[row, col] / 255.0
            idx = int(round(brightness * ramp_len))
            line_chars.append(RAMP[idx])
        lines.append("".join(line_chars))
    return lines


def render_preview_png(lines, out_path, font_size=14):
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()

    bbox = font.getbbox("M")
    char_w = bbox[2] - bbox[0] + 1
    char_h = font_size + 2

    cols = max(len(l) for l in lines)
    rows = len(lines)
    img_w = char_w * cols + 20
    img_h = char_h * rows + 20

    # white bg / near-black text: matches how a fenced code block renders on
    # GitHub's default light theme, which is where this preview will end up
    img = Image.new("RGB", (img_w, img_h), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    for r, line in enumerate(lines):
        draw.text((10, 10 + r * char_h), line, font=font, fill=(36, 41, 47))
    img.save(out_path)


def main():
    bgr = load_bgr(SRC)
    face_box = detect_face(bgr)
    cropped = crop_with_padding(bgr, face_box)
    fg_mask = remove_background_grabcut(cropped)
    lines = to_ascii(cropped, fg_mask, WIDTH_CHARS, VERTICAL_ASPECT)

    with open(ASCII_TXT_OUT, "w") as f:
        f.write("\n".join(lines) + "\n")

    render_preview_png(lines, PREVIEW_PNG_OUT)

    print(f"Wrote {ASCII_TXT_OUT} ({len(lines)} lines x {WIDTH_CHARS} cols)")
    print(f"Wrote {PREVIEW_PNG_OUT}")
    print()
    print("\n".join(lines))


if __name__ == "__main__":
    main()
