import numpy as np
import cv2

class GazeFeatures:
    @staticmethod
    def extract(landmarks):
        """
        Extracts robust gaze features from face landmarks.
        Uses iris position relative to eye corners and head orientation.
        """
        def get_dist(p1, p2):
            return np.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)

        # Eye landmarks (Mediapipe indices)
        # Left Eye: inner 133, outer 33, top 159, bottom 145, iris 468
        # Right Eye: inner 362, outer 263, top 386, bottom 374, iris 473
        
        # Left Eye Features
        l_inner, l_outer = landmarks[133], landmarks[33]
        l_top, l_bottom = landmarks[159], landmarks[145]
        l_iris = landmarks[468]
        
        l_width = get_dist(l_inner, l_outer)
        l_height = get_dist(l_top, l_bottom)
        
        l_rel_x = (l_iris.x - l_inner.x) / l_width if l_width > 0 else 0
        l_rel_y = (l_iris.y - l_top.y) / l_height if l_height > 0 else 0
        
        # Right Eye Features
        r_inner, r_outer = landmarks[362], landmarks[263]
        r_top, r_bottom = landmarks[386], landmarks[374]
        r_iris = landmarks[473]
        
        r_width = get_dist(r_inner, r_outer)
        r_height = get_dist(r_top, r_bottom)
        
        r_rel_x = (r_iris.x - r_inner.x) / r_width if r_width > 0 else 0
        r_rel_y = (r_iris.y - r_top.y) / r_height if r_height > 0 else 0
        
        # Head Pose proxy (using nose tip relative to face bounds)
        # 1: nose tip, 10: forehead, 152: chin, 234: left ear-ish, 454: right ear-ish
        nose = landmarks[1]
        face_left = landmarks[234]
        face_right = landmarks[454]
        face_top = landmarks[10]
        face_bottom = landmarks[152]
        
        head_w = get_dist(face_left, face_right)
        head_h = get_dist(face_top, face_bottom)
        
        head_x = (nose.x - face_left.x) / head_w if head_w > 0 else 0
        head_y = (nose.y - face_top.y) / head_h if head_h > 0 else 0

        return [l_rel_x, l_rel_y, r_rel_x, r_rel_y, head_x, head_y]

class KalmanFilter:
    def __init__(self, q=1e-5, r=1e-2):
        self.q = q  # process noise covariance
        self.r = r  # measurement noise covariance
        self.x = None  # estimated value
        self.p = 1.0   # error covariance

    def update(self, measurement):
        if self.x is None:
            self.x = measurement
            return self.x
        
        # Prediction
        self.p = self.p + self.q
        
        # Update
        k = self.p / (self.p + self.r)
        self.x = self.x + k * (measurement - self.x)
        self.p = (1 - k) * self.p
        
        return self.x
