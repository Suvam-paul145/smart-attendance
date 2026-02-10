import cv2
import os
import numpy as np

# Check for data
print(f"cv2 version: {cv2.__version__}")
data_path = cv2.data.haarcascades
print(f"Haarcascades path: {data_path}")

cascade_path = os.path.join(data_path, 'haarcascade_frontalface_default.xml')
if not os.path.exists(cascade_path):
    print("Haarcascade file not found!")
    # Try to find it elsewhere or download? 
    # Usually it is there.
else:
    print(f"Found cascade at {cascade_path}")
    face_cascade = cv2.CascadeClassifier(cascade_path)
    
    # Test on blank image
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    print(f"Faces detected: {len(faces)}")
