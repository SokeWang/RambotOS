import cv2
import mediapipe as mp
import numpy as np
from sklearn.svm import SVR
import pickle

mp_face_mesh = mp.solutions.face_mesh

class GazeTracker:
    def __init__(self):
        self.face_mesh = mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.calib_data = []
        self.model_x = SVR(kernel='rbf')
        self.model_y = SVR(kernel='rbf')

    def get_features(self, frame):
        results = self.face_mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if not results.multi_face_landmarks:
            return None
        
        landmarks = results.multi_face_landmarks[0].landmark
        # Iris landmarks (468-477 in MediaPipe)
        # Left eye center: 468, Right eye center: 473
        # We use relative position of iris to eye corners for gaze + head pose (nose tip 1, etc.)
        
        # Simple feature vector: [lx, ly, rx, ry, nx, ny, nz] (normalized)
        features = []
        for idx in [468, 473, 1]: # Left iris, Right iris, Nose tip
            features.extend([landmarks[idx].x, landmarks[idx].y, landmarks[idx].z])
        return np.array(features)

    def calibrate(self):
        # UI for 9-point calibration (simplified logic for the user)
        pass

tracker = GazeTracker()
