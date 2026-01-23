IMAGE_PATH = r"C:\Users\Keerthi\Downloads\Handwritten-Mathematical-Equation-Recognition-Using-CNN\dataset\val\(\(_375.png"
  # 🔁 change if needed
import cv2
import numpy as np
import tensorflow as tf

# ==============================
# CONFIG
# ==============================
IMG_SIZE = 45
MODEL_PATH = "eqn-detect1-with-brackets"   # trained binary model        # image to test
THRESHOLD = 0.35                            # IMPORTANT

# ==============================
# LOAD MODEL
# ==============================
print("🔄 Loading trained binary bracket model...")
model = tf.keras.models.load_model(MODEL_PATH)

# ==============================
# LOAD IMAGE
# ==============================
img = cv2.imread(IMAGE_PATH, cv2.IMREAD_GRAYSCALE)

if img is None:
    raise ValueError("❌ Image not found. Check IMAGE_PATH.")

# ==============================
# PREPROCESSING (CRITICAL)
# ==============================

# 1️⃣ Invert if background is dark
if np.mean(img) < 127:
    img = cv2.bitwise_not(img)

# 2️⃣ Threshold
_, img = cv2.threshold(
    img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
)

# 3️⃣ Find bounding box
coords = cv2.findNonZero(img)
if coords is None:
    print("❌ Empty image after thresholding")
    exit()

x, y, w, h = cv2.boundingRect(coords)
img = img[y:y+h, x:x+w]

# 4️⃣ Pad to square
size = max(w, h)
square = np.zeros((size, size), dtype=np.uint8)

x_offset = (size - w) // 2
y_offset = (size - h) // 2
square[y_offset:y_offset+h, x_offset:x_offset+w] = img

# 5️⃣ Resize
img = cv2.resize(square, (IMG_SIZE, IMG_SIZE))

# 6️⃣ Normalize
img = img.astype("float32") / 255.0
img = img.reshape(1, IMG_SIZE, IMG_SIZE, 1)

# ==============================
# PREDICT
# ==============================
pred = model.predict(img, verbose=0)[0][0]

print(f"📊 Confidence: {pred:.4f}")

if pred > THRESHOLD:
    print("✅ Bracket detected")
else:
    print("❌ No bracket detected")
