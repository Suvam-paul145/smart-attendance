import os
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import cv2
import logging

logger = logging.getLogger(__name__)

# Configuration
MIN_DETECTION_CONFIDENCE = 0.6
MODEL_FILENAME = 'blaze_face_short_range.tflite'
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', MODEL_FILENAME)

# State
_detector = None
_use_mediapipe = False # MediaPipe is unstable on Python 3.14 (threading/allocator issues)
_opencv_cascade = None

def _get_detector():
    """Lazy load the FaceDetector instance with fallback to OpenCV."""
    global _detector, _use_mediapipe, _opencv_cascade

    # If already decided to use OpenCV
    if not _use_mediapipe:
        if _opencv_cascade is None:
            _opencv_cascade = _load_opencv_cascade()
        return _opencv_cascade

    # Try to load MediaPipe
    if _detector is not None:
        return _detector

    try:
        if not os.path.exists(MODEL_PATH):
            logger.warning(f"Face detection model not found at {MODEL_PATH}")
            raise RuntimeError("Model file missing")

        base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
        options = vision.FaceDetectorOptions(
            base_options=base_options,
            min_detection_confidence=MIN_DETECTION_CONFIDENCE
        )
        _detector = vision.FaceDetector.create_from_options(options)
        logger.info("MediaPipe FaceDetector loaded successfully.")
        return _detector
    except Exception as e:
        logger.error(f"Failed to load MediaPipe FaceDetector: {e}. Falling back to OpenCV.")
        _use_mediapipe = False
        _opencv_cascade = _load_opencv_cascade()
        return _opencv_cascade

def _load_opencv_cascade():
    """Load OpenCV Haar Cascade."""
    try:
        cascade_path = os.path.join(cv2.data.haarcascades, 'haarcascade_frontalface_default.xml')
        if not os.path.exists(cascade_path):
             # Try local path or error
             logger.error("OpenCV Haar cascade file not found.")
             return None
        return cv2.CascadeClassifier(cascade_path)
    except Exception as e:
        logger.error(f"Failed to load OpenCV Cascade: {e}")
        return None

def detect_faces(image: np.ndarray) -> list[tuple[int, int, int, int]]:
    """
    Detect faces in an image using MediaPipe Tasks API with OpenCV fallback.
    
    Args:
        image: RGB numpy array (H, W, 3). Value range [0, 255].
        
    Returns:
        List of bounding boxes in format (top, right, bottom, left).
    """
    global _use_mediapipe
    
    detector = _get_detector()
    
    if _use_mediapipe and detector:
        try:
            # Ensure image is C-contiguous for MediaPipe
            if not image.flags['C_CONTIGUOUS']:
                image = np.ascontiguousarray(image)
                
            # Create MediaPipe Image object
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
            
            # Run detection
            detection_result = detector.detect(mp_image)
            
            faces = []
            for detection in detection_result.detections:
                bbox = detection.bounding_box
                x = bbox.origin_x
                y = bbox.origin_y
                w = bbox.width
                h = bbox.height
                faces.append((y, x + w, y + h, x))
            return faces
            
        except Exception as e:
            logger.error(f"MediaPipe detection failed: {e}. Falling back to OpenCV.")
            _use_mediapipe = False
            detector = _get_detector() # Will load OpenCV
    
    # Fallback to OpenCV
    if detector: # This is now the cascade classifier
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        # scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        detections = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        faces = []
        for (x, y, w, h) in detections:
            faces.append((y, x + w, y + h, x))
        return faces
    
    return []

