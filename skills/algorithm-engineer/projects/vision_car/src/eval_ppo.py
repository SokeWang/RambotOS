import gymnasium as gym
from gymnasium.wrappers import GrayscaleObservation, ResizeObservation
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import VecFrameStack, DummyVecEnv
import torch

def evaluate():
    env_id = "CarRacing-v3"
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    
    def make_env():
        # Must match training: continuous=False
        env = gym.make(env_id, render_mode="human", continuous=False)
        env = ResizeObservation(env, (64, 64))
        env = GrayscaleObservation(env, keep_dim=True)
        return env

    env = DummyVecEnv([make_env])
    env = VecFrameStack(env, n_stack=4, channels_order="last")

    # Load discrete model
    model_path = "../models/best_model" # Or ppo_car_racing_discrete
    try:
        model = PPO.load(model_path, device=device)
        print(f"Model loaded from {model_path}")
    except:
        print("Model not found. Please train with the new discrete config first.")
        return

    obs = env.reset()
    while True:
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, done, info = env.step(action)
        if done.any():
            obs = env.reset()

if __name__ == "__main__":
    evaluate()
