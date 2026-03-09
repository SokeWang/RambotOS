import cv2
import mediapipe as mp
import numpy as np
import time
import pickle

# --- Configuration ---
CALIBRATION_POINTS = [
    (0.1, 0.1), (0.5, 0.1), (0.9, 0.1),
    (0.1, 0.5), (0.5, 0.5), (0.9, 0.5),
    (0.1, 0.9), (0.5, 0.9), (0.9, 0.9)
]
SCREEN_W, SCREEN_H = 1728, 1117 # MBP 14-inch default (Approx)

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

def get_eye_features(landmarks):
    # Left Iris: 468, 469, 470, 471, 472 (Center is 468)
    # Right Iris: 473, 474, 475, 476, 477 (Center is 473)
    # Eye corners (Left: 33, 133; Right: 362, 263)
    def iris_pos(center_idx, inner_idx, outer_idx):
        center = landmarks[center_idx]
        inner = landmarks[inner_idx]
        outer = landmarks[outer_idx]
        # Relative horizontal position (0-1)
        rel_x = (center.x - inner.x) / (outer.x - inner.x)
        # Relative vertical (simplified based on top/bottom eyelids)
        return rel_x, center.y

    lx, ly = iris_pos(468, 33, 133)
    rx, ry = iris_pos(473, 362, 263)

    # Simplified Head Pose (Nose 1, Chin 152, L-Eye 33, R-Eye 263)
    # Pitch/Yaw approximation from nose/eye relationship
    head_yaw = landmarks[1].x - 0.5
    head_pitch = landmarks[1].y - landmarks[152].y
    
    return [lx, ly, rx, ry, head_yaw, head_pitch]

def run_calibration():
    cap = cv2.VideoCapture(0)
    data_points = []
    
    cv2.namedWindow("Calibration", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("Calibration", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    print("Look at the red dots and wait.")
    
    for pt in CALIBRATION_POINTS:
        start_time = time.time()
        while time.time() - start_time < 2.0: # 2 seconds per point
            ret, frame = cap.read()
            if not ret: break
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb)
            
            # Draw UI
            canvas = np.zeros((SCREEN_H, SCREEN_W, 3), dtype=np.uint8)
            cx, cy = int(pt[0] * SCREEN_W), int(pt[1] * SCREEN_H)
            cv2.circle(canvas, (cx, cy), 20, (0, 0, 255), -1)
            cv2.putText(canvas, "STARE AT DOT", (cx-50, cy-40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
            cv2.imshow("Calibration", canvas)
            
            if results.multi_face_landmarks:
                feat = get_eye_features(results.multi_face_landmarks[0].landmark)
                # Only collect data in the last 1 second to ensure user is focused
                if time.time() - start_time > 1.0:
                    data_points.append({'feat': feat, 'target': [cx, cy]})
            
            if cv2.waitKey(1) & 0xFF == ord('q'): return

    cap.release()
    cv2.destroyAllWindows()
    
    with open("calibration_data.pkl", "wb") as f:
        pickle.dump(data_points, f)
    print(f"Collected {len(data_points)} samples. Training...")

if __name__ == "__main__":
    run_calibration()
