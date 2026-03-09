import cv2
import mediapipe as mp
import numpy as np
import os
import csv
import time
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from utils import GazeFeatures

# Paths
MODEL_PATH = "models/face_landmarker.task"
DATA_FILE = "data/calibration_data.csv"
os.makedirs("data", exist_ok=True)

# Initialize Mediapipe
base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    output_face_blendshapes=True,
    num_faces=1)
detector = vision.FaceLandmarker.create_from_options(options)

WINDOW_NAME = "Precision Calibration"
cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

screen_width = 1440
screen_height = 900

points = [
    (0.1, 0.1), (0.5, 0.1), (0.9, 0.1),
    (0.1, 0.5), (0.5, 0.5), (0.9, 0.5),
    (0.1, 0.9), (0.5, 0.9), (0.9, 0.9)
]

def capture_burst(cap, detector, num_frames=15):
    """Captures multiple frames and averages features for noise reduction."""
    burst_features = []
    while len(burst_features) < num_frames:
        ret, frame = cap.read()
        if not ret: break
        # Flip the frame horizontally for a mirrored view
        frame = cv2.flip(frame, 1)
        
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        res = detector.detect(mp_image)
        
        if res.face_landmarks:
            feat = GazeFeatures.extract(res.face_landmarks[0])
            burst_features.append(feat)
            
    return np.mean(burst_features, axis=0).tolist()

def main():
    cap = cv2.VideoCapture(1)
    # Set high resolution for better iris detail
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    current_point_idx = 0
    print("Precision Calibration: Hold head STILL, use only eyes.")

    with open(DATA_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["screen_x", "screen_y", "lrx", "lry", "rrx", "rry", "hx", "hy"])

        while cap.isOpened() and current_point_idx < len(points):
            ret, frame = cap.read()
            if not ret: break
            # Flip frame for mirror consistency
            frame = cv2.flip(frame, 1)
            
            canvas = np.zeros((screen_height, screen_width, 3), dtype=np.uint8)
            px, py = points[current_point_idx]
            sx, sy = int(px * screen_width), int(py * screen_height)
            
            cv2.circle(canvas, (sx, sy), 15, (0, 0, 255), -1)
            cv2.circle(canvas, (sx, sy), 25, (0, 0, 255), 2)
            cv2.putText(canvas, f"Point {current_point_idx+1}/9: Stare & Space", (50, 50), 1, 2, (255,255,255), 2)
            
            cv2.imshow(WINDOW_NAME, canvas)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord(' '):
                print(f"Capturing burst for point {current_point_idx+1}...")
                feat = capture_burst(cap, detector)
                writer.writerow([sx, sy] + feat)
                current_point_idx += 1
            elif key == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
