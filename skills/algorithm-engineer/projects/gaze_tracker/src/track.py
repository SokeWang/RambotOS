import cv2
import mediapipe as mp
import numpy as np
import joblib
import os
from utils import GazeFeatures, KalmanFilter
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# --- Settings ---
CAMERA_ID = 1  # External camera
MODEL_PATH = "models/gaze_model.pkl"
TASK_FILE = "face_landmarker.task"

def track():
    if not os.path.exists(MODEL_PATH):
        print(f"Model not found at {MODEL_PATH}. Please run train.py first.")
        return

    # Load Model (dict containing x and y models)
    try:
        models = joblib.load(MODEL_PATH)
        model_x = models['x']
        model_y = models['y']
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    # Setup MediaPipe
    if not os.path.exists(TASK_FILE):
        print(f"Task file not found at {TASK_FILE}.")
        print("Please download it from: https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task")
        return

    base_options = python.BaseOptions(model_asset_path=TASK_FILE)
    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        output_face_blendshapes=False,
        output_facial_transformation_matrixes=True,
        num_faces=1
    )
    detector = vision.FaceLandmarker.create_from_options(options)

    # Kalman Filters for smoothness
    kf_x = KalmanFilter(q=0.01, r=0.5)
    kf_y = KalmanFilter(q=0.01, r=0.5)

    cap = cv2.VideoCapture(CAMERA_ID)
    cv2.namedWindow("Gaze Tracker", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("Gaze Tracker", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    print("Tracking started. Press 'q' to exit.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        detection_result = detector.detect(mp_image)

        black_screen = np.zeros((1080, 1920, 3), dtype=np.uint8)

        if detection_result.face_landmarks:
            landmarks = detection_result.face_landmarks[0]
            features = GazeFeatures.extract(landmarks)
            
            # Predict
            X = np.array([features])
            pred_x = model_x.predict(X)[0]
            pred_y = model_y.predict(X)[0]

            # Smooth
            smooth_x = int(kf_x.update(pred_x))
            smooth_y = int(kf_y.update(pred_y))

            # Display on screen
            cv2.circle(black_screen, (smooth_x, smooth_y), 20, (0, 255, 0), -1)
            cv2.putText(black_screen, f"X:{smooth_x} Y:{smooth_y}", (50, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        cv2.imshow("Gaze Tracker", black_screen)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    track()
