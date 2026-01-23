import cv2
import numpy as np
import os
import random
from PIL import Image, ImageDraw, ImageFont

# ================= CONFIG =================
OUTPUT_DIR = "dataset/train"
IMG_SIZE = 64
SAMPLES_PER_CLASS = 1000

FONTS = [
    "arial.ttf",
    "times.ttf",
    "calibri.ttf"
]

SYMBOLS = {
    "(": "(",
    ")": ")"
}

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ================= HELPERS =================
def add_noise(img):
    noise = np.random.randint(0, 40, img.shape, dtype="uint8")
    return cv2.add(img, noise)

def distort(img):
    h, w = img.shape
    dx = random.randint(-3, 3)
    dy = random.randint(-3, 3)
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(img, M, (w, h), borderValue=255)

# ================= GENERATOR =================
for label, symbol in SYMBOLS.items():
    class_dir = os.path.join(OUTPUT_DIR, label)
    os.makedirs(class_dir, exist_ok=True)

    for i in range(SAMPLES_PER_CLASS):
        img = Image.new("L", (IMG_SIZE, IMG_SIZE), 255)
        draw = ImageDraw.Draw(img)

        font_path = random.choice(FONTS)
        font_size = random.randint(40, 55)

        try:
            font = ImageFont.truetype(font_path, font_size)
        except:
            continue

        # ✅ FIXED PART (Pillow >= 10)
        bbox = draw.textbbox((0, 0), symbol, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]

        x = (IMG_SIZE - w) // 2 + random.randint(-3, 3)
        y = (IMG_SIZE - h) // 2 + random.randint(-3, 3)

        draw.text((x, y), symbol, font=font, fill=0)

        img = np.array(img)
        img = add_noise(img)
        img = distort(img)

        save_path = os.path.join(class_dir, f"{label}_{i}.png")
        cv2.imwrite(save_path, img)

print("✅ Bracket dataset generated successfully")
