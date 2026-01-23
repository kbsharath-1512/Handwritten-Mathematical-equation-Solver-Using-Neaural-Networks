import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.optimizers import Adam

# ================= CONFIG =================
IMG_SIZE = 45
BATCH_SIZE = 32
EPOCHS = 15

TRAIN_DIR = "dataset/train"
VAL_DIR = "dataset/val"

# ================= MODEL (REDUCED CAPACITY) =================
model = Sequential([
    Conv2D(32, (3,3), activation="relu", input_shape=(IMG_SIZE, IMG_SIZE, 1)),
    MaxPooling2D(2),

    Conv2D(64, (3,3), activation="relu"),
    MaxPooling2D(2),

    Conv2D(64, (3,3), activation="relu"),   # 🔻 reduced filters
    MaxPooling2D(2),

    Flatten(),
    Dense(64, activation="relu"),           # 🔻 smaller dense
    Dropout(0.5),                            # 🔥 key fix
    Dense(1, activation="sigmoid")
])

model.compile(
    optimizer=Adam(learning_rate=3e-5),     # 🔻 lower LR
    loss="binary_crossentropy",
    metrics=["accuracy"]
)

model.summary()

# ================= DATA (GENTLE AUGMENTATION) =================
train_gen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=5,
    zoom_range=0.05,
    width_shift_range=0.03,
    height_shift_range=0.03
)

val_gen = ImageDataGenerator(rescale=1./255)

train_data = train_gen.flow_from_directory(
    TRAIN_DIR,
    target_size=(IMG_SIZE, IMG_SIZE),
    color_mode="grayscale",
    batch_size=BATCH_SIZE,
    class_mode="binary"
)

val_data = val_gen.flow_from_directory(
    VAL_DIR,
    target_size=(IMG_SIZE, IMG_SIZE),
    color_mode="grayscale",
    batch_size=BATCH_SIZE,
    class_mode="binary"
)

# ================= TRAIN =================
model.fit(
    train_data,
    validation_data=val_data,
    epochs=EPOCHS
)

# ================= SAVE =================
model.save("bracket_binary_model_fixed")
print("✅ Fixed binary bracket model saved")
