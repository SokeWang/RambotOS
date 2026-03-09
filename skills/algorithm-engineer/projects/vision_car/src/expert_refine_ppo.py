import gymnasium as gym
from gymnasium.wrappers import GrayscaleObservation, ResizeObservation
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import VecFrameStack, DummyVecEnv
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.monitor import Monitor
import torch
import os
import numpy as np

class ExpertRewardWrapper(gym.RewardWrapper):
    """
    Expert Level: Fixing Oversteering and Cutting.
    """
    def __init__(self, env):
        super().__init__(env)
        self.current_action = 0

    def step(self, action):
        # Action 1: Left, Action 2: Right
        self.current_action = action
        return super().step(action)

    def reward(self, reward):
        # 1. Grass is Lava (Stay on track)
        if reward < 0:
            reward *= 5.0
        
        # 2. Track Progress Bonus
        if reward > 0:
            reward *= 2.0

        # 3. Oversteer Penalty (Heuristic)
        # Penalty for active steering to prevent over-rotation (holding the key)
        if self.current_action in [1, 2]:
            reward -= 0.05 
            
        return reward

def make_env(env_id, render_mode=None):
    def _init():
        env = gym.make(env_id, render_mode=render_mode, continuous=False)
        env = Monitor(env)
        env = ExpertRewardWrapper(env)
        env = ResizeObservation(env, (64, 64))
        env = GrayscaleObservation(env, keep_dim=True)
        return env
    return _init

def expert_refine():
    env_id = "CarRacing-v3"
    model_dir = "../models/"
    model_load_path = os.path.join(model_dir, "best_model")
    model_save_path = os.path.join(model_dir, "ppo_car_racing_expert")
    log_dir = "./ppo_car_racing_tensorboard/"
    
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Expert Refinement: Fixing Oversteer on {device}")
    
    train_env = DummyVecEnv([make_env(env_id, render_mode="rgb_array")])
    train_env = VecFrameStack(train_env, n_stack=4, channels_order="last")

    eval_env = DummyVecEnv([make_env(env_id, render_mode="rgb_array")])
    eval_env = VecFrameStack(eval_env, n_stack=4, channels_order="last")

    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=model_dir,
        log_path=log_dir,
        eval_freq=2000,
        deterministic=True,
        render=False
    )

    if os.path.exists(f"{model_load_path}.zip"):
        print(f"Loading best model for EXPERT refinement: {model_load_path}")
        model = PPO.load(model_load_path, env=train_env, device=device)
        
        # Expert Parameters: Micro-precision
        model.learning_rate = 1e-5 
        model.ent_coef = 0.0005    
    else:
        print("Best model not found. Run pro_refine_ppo.py first.")
        return

    print("EXPERT Stage: Fixing Oversteering (Tapping instead of Holding)...")
    model.learn(
        total_timesteps=200000, 
        callback=eval_callback,
        progress_bar=True, 
        reset_num_timesteps=False
    )
    
    model.save(model_save_path)
    print(f"Expert model saved to {model_save_path}")

if __name__ == "__main__":
    expert_refine()
