import gymnasium as gym
from gymnasium.wrappers import GrayscaleObservation, ResizeObservation
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import VecFrameStack, DummyVecEnv
import os

def train():
    env_id = "CarRacing-v3"
    
    def make_env():
        # Ensure we use rgb_array for training
        env = gym.make(env_id, render_mode="rgb_array")
        env = ResizeObservation(env, (64, 64))
        env = GrayscaleObservation(env, keep_dim=True)
        return env

    # DummyVecEnv is needed for VecFrameStack
    env = DummyVecEnv([make_env])
    # Use the SB3 VecFrameStack which is more stable for this use case
    env = VecFrameStack(env, n_stack=4, channels_order="last")

    model = PPO(
        "CnnPolicy", 
        env, 
        verbose=1, 
        learning_rate=3e-4,
        n_steps=512, # Small n_steps for stability/memory
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        tensorboard_log="./ppo_car_racing_tensorboard/"
    )

    print("Running smoke test (100 steps)...")
    model.learn(total_timesteps=100)
    print("Smoke test passed.")
    
    # Save a dummy model to ensure path works
    model_path = "../models/ppo_car_racing"
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    model.save(model_path)
    print(f"Verified training pipeline. Ready for full run.")

if __name__ == "__main__":
    train()
