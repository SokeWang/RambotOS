import numpy as np
import cv2
from env import BEVCarEnv

def run_pid_agent():
    env = BEVCarEnv(render_mode="human")
    obs, info = env.reset()
    
    total_reward = 0
    terminated = truncated = False
    
    # PID Constants
    Kp = 3.8
    Ki = 0.02
    Kd = 1.6
    
    prev_error = 0
    integral = 0
    last_known_error = 0
    
    print("Starting Advanced Control-Flow Pilot...")
    
    while not (terminated or truncated):
        bev = env.get_bev(obs)
        near_error, far_error, debug_view = env.detect_road(bev)
        
        if env.step_count < 45:
            action = np.array([0, 0.1, 0])
        elif near_error is None:
            # LOST MODE: Brake and steer hard in last known direction
            steering = 1.0 if last_known_error > 0 else -1.0
            action = np.array([steering, 0.0, 0.6])
            integral = 0
        else:
            # PID Steering with Look-ahead
            error = near_error * 0.5 + far_error * 0.5
            integral += error
            integral = np.clip(integral, -5, 5)
            derivative = error - prev_error
            steering = np.clip(Kp * error + Ki * integral + Kd * derivative, -1.0, 1.0)
            
            # Curvature-based Speed Control
            curvature = abs(far_error - near_error)
            is_sharp = curvature > 0.25 or abs(far_error) > 0.5
            
            if is_sharp:
                throttle = 0.0
                brake = 0.2 if abs(steering) > 0.5 else 0.1
            else:
                throttle = 0.3
                brake = 0
                
            action = np.array([steering, throttle, brake])
            prev_error = error
            last_known_error = error
            
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        
        # Visualization
        cv2.imshow("Detection Logic", cv2.resize(debug_view, (400, 400)))
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    env.close()
    cv2.destroyAllWindows()
    print(f"Trial Finished. Total Reward: {total_reward:.2f}")

if __name__ == "__main__":
    run_pid_agent()
