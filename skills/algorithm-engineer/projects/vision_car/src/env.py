import gymnasium as gym
import numpy as np
import cv2

class BEVCarEnv(gym.Wrapper):
    def __init__(self, render_mode="rgb_array"):
        env = gym.make("CarRacing-v3", render_mode=render_mode)
        super(BEVCarEnv, self).__init__(env)
        self.last_error = 0
        self.step_count = 0

    def reset(self, **kwargs):
        self.last_error = 0
        self.step_count = 0
        return self.env.reset(**kwargs)

    def get_bev(self, raw_obs):
        # Focus on the area in front of the car
        # In CarRacing-v3, the car is roughly at [66, 48] in a 96x96 view
        h, w = raw_obs.shape[:2]
        crop = raw_obs[0:84, 0:96] # Remove bottom dashboard
        bev = cv2.resize(crop, (128, 128))
        gray = cv2.cvtColor(bev, cv2.COLOR_RGB2GRAY)
        return gray

    def detect_road(self, bev):
        # Pre-process: Blur to reduce noise from track edges
        blurred = cv2.GaussianBlur(bev, (5, 5), 0)
        mask = cv2.inRange(blurred, 95, 125)
        
        scan_lines = [110, 100, 90, 80, 70, 60, 50, 40]
        centers = {}
        viz_points = []
        for y in scan_lines:
            pixels = np.where(mask[y, :] > 0)[0]
            if len(pixels) > 5:
                center = np.mean(pixels)
                centers[y] = center
                viz_points.append((int(center), y))
        
        if not centers:
            return None, None, mask
            
        near_y = max(centers.keys())
        far_y = min(centers.keys())
        
        near_error = (centers[near_y] - 64) / 64.0
        far_error = (centers[far_y] - 64) / 64.0
        
        # Draw for visualization
        debug_view = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        for pt in viz_points:
            cv2.circle(debug_view, pt, 2, (0, 0, 255), -1)
            
        return near_error, far_error, debug_view

    def step(self, action=None):
        self.step_count += 1
        # If no action provided, we are in rule-based mode
        # The test script will handle the PID logic using the helper methods
        return self.env.step(action)
