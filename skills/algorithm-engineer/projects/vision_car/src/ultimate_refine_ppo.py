import gymnasium as gym
from gymnasium.wrappers import GrayscaleObservation, ResizeObservation
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import VecFrameStack, DummyVecEnv
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.utils import constant_fn
import torch
import os

class UltimateRewardWrapper(gym.Wrapper):
    def __init__(self, env):
        super().__init__(env)
        self.negative_reward_streak = 0
        self.max_negative_streak = 50

    def reset(self, **kwargs):
        self.negative_reward_streak = 0
        return self.env.reset(**kwargs)

    def step(self, action):
        obs, reward, terminated, truncated, info = self.env.step(action)
        
        if reward < 0:
            self.negative_reward_streak += 1
            reward *= 15.0
        else:
            self.negative_reward_streak = 0
            reward *= 2.5
            
        if self.negative_reward_streak > self.max_negative_streak:
            reward -= 150.0
            terminated = True 

        return obs, reward, terminated, truncated, info

def make_env(env_id, render_mode=None):
    def _init():
        env = gym.make(env_id, render_mode=render_mode, continuous=False)
        env = Monitor(env)
        env = UltimateRewardWrapper(env)
        env = ResizeObservation(env, (64, 64))
        env = GrayscaleObservation(env, keep_dim=True)
        return env
    return _init

def ultimate_refine():
    env_id = "CarRacing-v3"
    model_dir = "../models/"
    model_load_path = os.path.join(model_dir, "best_model")
    model_save_path = os.path.join(model_dir, "ppo_car_racing_ultimate")
    log_dir = "./ppo_car_racing_tensorboard/"
    
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Ultimate Refinement: Fixing Direction on {device}")
    
    train_env = DummyVecEnv([make_env(env_id, render_mode="rgb_array")])
    train_env = VecFrameStack(train_env, n_stack=4, channels_order="last")

    eval_env = DummyVecEnv([make_env(env_id, render_mode="rgb_array")])
    eval_env = VecFrameStack(eval_env, n_stack=4, channels_order="last")

    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=model_dir,
        log_path=log_dir,
        eval_freq=2500,
        deterministic=True,
        render=False
    )

    if os.path.exists(f"{model_load_path}.zip"):
        model = PPO.load(model_load_path, env=train_env, device=device)
        # SB3 expects schedules (callables) for these attributes
        model.learning_rate = 8e-6
        model.lr_schedule = constant_fn(8e-6)
        model.clip_range = constant_fn(0.1)
        model.ent_coef = 0.0001
    else:
        print("Required base model not found.")
        return

    print("ULTIMATE Stage: Training with Kill-Switch and High Penalty...")
    model.learn(
        total_timesteps=400000, 
        callback=eval_callback,
        progress_bar=False, 
        reset_num_timesteps=False
    )
    
    model.save(model_save_path)
    print(f"Ultimate model saved to {model_save_path}")

if __name__ == "__main__":
    ultimate_refine()
