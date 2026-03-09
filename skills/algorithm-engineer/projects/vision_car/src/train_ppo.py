import gymnasium as gym
from gymnasium.wrappers import GrayscaleObservation, ResizeObservation
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import VecFrameStack, DummyVecEnv
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.monitor import Monitor
import torch
import os

def make_env(env_id, render_mode=None):
    def _init():
        # Use discrete actions to avoid continuous space collapse
        env = gym.make(env_id, render_mode=render_mode, continuous=False)
        env = Monitor(env)
        env = ResizeObservation(env, (64, 64))
        env = GrayscaleObservation(env, keep_dim=True)
        return env
    return _init

def train():
    env_id = "CarRacing-v3"
    model_dir = "../models/"
    model_path = os.path.join(model_dir, "ppo_car_racing_discrete")
    log_dir = "./ppo_car_racing_tensorboard/"
    
    os.makedirs(model_dir, exist_ok=True)
    
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Using device: {device}")
    
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

    # Note: Switching to discrete actions requires a new model architecture
    if os.path.exists(f"{model_path}.zip"):
        print(f"Resuming from {model_path}...")
        model = PPO.load(model_path, env=train_env, device=device)
    else:
        print("Starting new training with Discrete Action Space...")
        model = PPO(
            "CnnPolicy", 
            train_env, 
            verbose=1, 
            learning_rate=2e-4, # Lowered for stability
            n_steps=2048,       # Increased for better advantage estimation
            batch_size=128,     # Larger batch for smoother gradients
            n_epochs=10,
            gamma=0.99,
            ent_coef=0.05,      # Significantly increased to break local optima
            device=device,
            tensorboard_log=log_dir
        )

    print("Breaking local optimum: Discrete actions + Higher entropy.")
    model.learn(
        total_timesteps=1000000, 
        callback=eval_callback,
        progress_bar=True, 
        reset_num_timesteps=False
    )
    
    model.save(model_path)

if __name__ == "__main__":
    train()
