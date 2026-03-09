import numpy as np
import cv2
from env import BEVCarEnv
import os

def validate_logic():
    print("Validating logic (Headless)...")
    # Use rgb_array for headless validation
    env = BEVCarEnv(render_mode="rgb_array")
    obs, info = env.reset()
    
    # Run for 60 steps to pass the zoom animation
    for i in range(60):
        bev = env.get_bev(obs)
        near_error, far_error, debug_view = env.detect_road(bev)
        
        if env.step_count < 45 or near_error is None:
            action = np.array([0.0, 0.1, 0.0])
        else:
            action = np.array([0.0, 0.2, 0.0])
            
        obs, reward, terminated, truncated, info = env.step(action)
        if i % 10 == 0:
            print(f"Step {i}: Road detected: {near_error is not None}")
            
    print("Logic validation successful. No crashes.")
    env.close()

if __name__ == "__main__":
    validate_logic()
