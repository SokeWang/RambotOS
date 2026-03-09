import cv2
import numpy as np
import pickle
import os
from insightface.app import FaceAnalysis

def register_user(output_path="data/user_profile.pkl"):
    # Initialize InsightFace
    app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider']) # Use CPU for registration for stability
    app.prepare(ctx_id=0, det_size=(640, 640))

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    print("--- Registration Process ---")
    print("Please look directly at the camera. Press 's' to capture your face or 'q' to quit.")

    embeddings = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        faces = app.get(frame)
        
        # Draw face boxes for feedback
        display_frame = frame.copy()
        for face in faces:
            bbox = face.bbox.astype(int)
            cv2.rectangle(display_frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
            cv2.putText(display_frame, "Face Detected", (bbox[0], bbox[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        cv2.imshow("Registration - Press 's' to save", display_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('s') and len(faces) > 0:
            # Sort by box area to get the closest face if multiple
            faces.sort(key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]), reverse=True)
            embeddings.append(faces[0].normed_embedding)
            print(f"Captured face {len(embeddings)}/5")
            if len(embeddings) >= 5:
                break
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    if embeddings:
        avg_embedding = np.mean(embeddings, axis=0)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            pickle.dump(avg_embedding, f)
        print(f"Successfully registered. Profile saved to {output_path}")
    else:
        print("Registration cancelled or failed.")

if __name__ == "__main__":
    register_user()
