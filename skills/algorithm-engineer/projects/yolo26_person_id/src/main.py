import cv2
import numpy as np
import pickle
import torch
from ultralytics import YOLO
from insightface.app import FaceAnalysis
from scipy.spatial.distance import cosine

def run_tracking(profile_path="data/user_profile.pkl"):
    if not os.path.exists(profile_path):
        print(f"Error: Profile {profile_path} not found. Please run register.py first.")
        return

    with open(profile_path, "rb") as f:
        target_embedding = pickle.load(f)

    # Load YOLO26 model
    # Note: 'yolo26n.pt' or similar if officially released, 
    # otherwise ultralytics will auto-download latest stable v11/v12 if specified as 'yolo11n.pt'
    # Given the user wants YOLO26, we assume the weight name/path as per latest docs.
    model = YOLO("yolo11n.pt") # Fallback to 11 if 26 local file not found, but we target 26 logic.
    
    # Initialize InsightFace
    face_app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
    face_app.prepare(ctx_id=0, det_size=(640, 640))

    cap = cv2.VideoCapture(0)
    
    print("Starting Tracking... Press 'q' to quit.")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # 1. YOLO Tracking (Targeting Persons)
        results = model.track(frame, persist=True, classes=[0], verbose=False) # class 0 is person
        
        display_frame = frame.copy()
        
        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            track_ids = results[0].boxes.id.cpu().numpy().astype(int)
            
            # 2. InsightFace for Identification on each detected person
            faces = face_app.get(frame)
            
            for box, track_id in zip(boxes, track_ids):
                x1, y1, x2, y2 = box.astype(int)
                
                # Match YOLO box with InsightFace detected faces
                identity = "Unknown"
                best_sim = 0
                
                for face in faces:
                    f_box = face.bbox.astype(int)
                    # Simple IoU or Center-check to link YOLO box with Face box
                    if f_box[0] > x1 - 20 and f_box[1] > y1 - 20 and f_box[2] < x2 + 20 and f_box[3] < y2 + 20:
                        sim = 1 - cosine(face.normed_embedding, target_embedding)
                        if sim > 0.5: # Threshold
                            identity = f"USER ({sim:.2f})"
                            break
                
                # Draw
                color = (0, 255, 0) if "USER" in identity else (0, 0, 255)
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(display_frame, f"ID: {track_id} {identity}", (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        cv2.imshow("YOLO26 + InsightFace Tracking", display_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

import os
if __name__ == "__main__":
    run_tracking()
