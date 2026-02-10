import cv2
import numpy as np
import sys
import os

import logging

# Configure logging to see the fallback messages
logging.basicConfig(level=logging.INFO)

# Add project root to path
sys.path.append(os.getcwd())

from app.ml.face_detector import detect_faces

# Create a blank black image
img = np.zeros((100, 100, 3), dtype=np.uint8)

print("Testing detection on blank image...")
try:
    faces = detect_faces(img)
    print(f"Detection successful. Found {len(faces)} faces (expected 0).")
except Exception as e:
    print(f"Detection failed: {e}")
    import traceback
    traceback.print_exc()
