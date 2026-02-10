import urllib.request
import os

MODELS_DIR = "app/ml/models"
os.makedirs(MODELS_DIR, exist_ok=True)

models = {
    "blaze_face_short_range.tflite": "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite",
    "face_embedder.tflite": "https://storage.googleapis.com/mediapipe-models/face_embedder/face_embedder/float16/1/face_embedder.tflite"
}

for name, url in models.items():
    print(f"Downloading {name}...")
    try:
        urllib.request.urlretrieve(url, os.path.join(MODELS_DIR, name))
        print(f"Downloaded {name}")
    except Exception as e:
        print(f"Failed to download {name}: {e}")
