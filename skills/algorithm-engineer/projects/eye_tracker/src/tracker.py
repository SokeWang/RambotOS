import pickle
import numpy as np
from sklearn.multioutput import MultiOutputRegressor
from sklearn.svm import SVR
import cv2
import mediapipe as mp
import time

# Same as calibration for consistency
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

def get_eye_features(landmarks):
    # Normalized Iris Position Relative to Eyelids
    # Simplified head-eye features (X, Y, Pitch, Yaw)
    lx = landmarks[468].x - landmarks[33].x
    ly = landmarks[468].y - landmarks[159].y # Top eyelid 159
    rx = landmarks[473].x - landmarks[362].x
    ry = landmarks[473].y - landmarks[386].y # Top eyelid 386
    hx = landmarks[1].x - 0.5 # Nose offset
    hy = landmarks[1].y - 0.5
    return [lx, ly, rx, ry, hx, hy]

def train_model():
    with open("calibration_data.pkl", "rb") as f:
        data = pickle.load(f)
    
    X = np.array([d['feat'] for d in data])
    y = np.array([d['target'] for d in data])
    
    # Using SVR with RBF kernel for non-linear mapping
    model = MultiOutputRegressor(SVR(kernel='rbf', C=1e4, gamma=0.1))
    model.fit(X, y)
    
    with open("gaze_model.pkl", "wb") as f:
        pickle.dump(model, f)
    print("Model trained and saved.")

def track():
    with open("gaze_model.pkl", "rb") as f:
        model = pickle.load(f)
    
    cap = cv2.VideoCapture(0)
    # Using a simple moving average to smooth output
    history = []
    
    while True:
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)
        
        # Display window
        canvas = np.zeros((1117, 1728, 3), dtype=np.uint8)
        
        if results.multi_face_landmarks:
            feat = get_eye_features(results.multi_face_landmarks[0].landmark)
            pred = model.predict([feat])[0]
            
            # Smoothing
            history.append(pred)
            if len(history) > 5: history.pop(0)
            smooth_pred = np.mean(history, axis=0).astype(int)
            
            # Draw Gaze Target
            cv2.circle(canvas, (smooth_pred[0], smooth_pred[1]), 30, (0, 255, 0), -1)
            cv2.putText(canvas, f"Target: {smooth_pred}", (10, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        cv2.imshow("Gaze Tracker", canvas)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    train_model()
    track()
