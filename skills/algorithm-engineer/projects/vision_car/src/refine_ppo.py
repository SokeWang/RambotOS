import gymnasium as gym
from gymnasium.wrappers import GrayscaleObservation, ResizeObservation
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import VecFrameStack, DummyVecEnv
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.monitor import Monitor
import torch
import os
import numpy as np

class RefinedRewardWrapper(gym.RewardWrapper):
    def __init__(self, env):
        super().__init__(env)

    def reward(self, reward):
        # Increased penalty for off-track behavior (negative rewards)
        if reward < 0:
            return reward * 1.5 
        return reward

def make_env(env_id, render_mode=None):
    def _init():
        env = gym.make(env_id, render_mode=render_mode, continuous=False)
        env = Monitor(env)
        env = RefinedRewardWrapper(env)
        env = ResizeObservation(env, (64, 64))
        env = GrayscaleObservation(env, keep_dim=True)
        return env
    return _init

def refine():
    env_id = "CarRacing-v3"
    model_dir = "../models/"
    model_load_path = os.path.join(model_dir, "best_model")
    model_save_path = os.path.join(model_dir, "ppo_car_racing_refined")
    log_dir = "./ppo_car_racing_tensorboard/"
    
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Refining on device: {device}")
    
    train_env = DummyVecEnv([make_env(env_id, render_mode="human")])
    train_env = VecFrameStack(train_env, n_stack=4, channels_order="last")

    eval_env = DummyVecEnv([make_env(env_id, render_mode="rgb_array")])
    eval_env = VecFrameStack(eval_env, n_stack=4, channels_order="last")

    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=model_dir,
        log_path=log_dir,
        eval_freq=5000,
        deterministic=True,
        render=False
    )

    if os.path.exists(f"{model_load_path}.zip"):
        print(f"Loading best model for refinement: {model_load_path}")
        model = PPO.load(model_load_path, env=train_env, device=device)
        
        # FIXED: n_steps must match the original buffer size (2048) unless manually re-initialized
        # Changing model.n_steps after loading doesn't resize the existing rollout_buffer.
        model.learning_rate = 5e-5  
        model.ent_coef = 0.005     
        # Keeping model.n_steps at 2048 to avoid buffer overflow
        model.batch_size = 128     
    else:
        print("Best model not found. Please run train_ppo.py first.")
        return

    print("Refinement Phase: Stabilizing policy and improving precision...")
    model.learn(
        total_timesteps=300000, 
        callback=eval_callback,
        progress_bar=True, 
        reset_num_timesteps=False
    )
    
    model.save(model_save_path)
    print(f"Refined model saved to {model_save_path}")

if __name__ == "__main__":
    refine()
