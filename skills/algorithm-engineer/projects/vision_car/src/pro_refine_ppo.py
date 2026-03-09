import gymnasium as gym
from gymnasium.wrappers import GrayscaleObservation, ResizeObservation
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import VecFrameStack, DummyVecEnv
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.monitor import Monitor
import torch
import os

class ProRewardWrapper(gym.RewardWrapper):
    """
    The 'FastRender' logic: Moving from ASLOP to precision.
    Focuses on punishing grass-touching and rewarding clean lines.
    """
    def reward(self, reward):
        # CarRacing-v3 rewards: -0.1 per frame, +1000/N per track tile.
        # If reward is negative, it's either time-leak or off-track.
        if reward < 0:
            return reward * 5.0  # Hyper-penalty for grass (The 'Grass is Lava' approach)
        
        # If reward is positive, it means we hit a new track tile.
        # Boost this to encourage staying on the path over cutting corners.
        if reward > 0:
            return reward * 2.0
            
        return reward

def make_env(env_id, render_mode=None):
    def _init():
        env = gym.make(env_id, render_mode=render_mode, continuous=False)
        env = Monitor(env)
        env = ProRewardWrapper(env)
        env = ResizeObservation(env, (64, 64))
        env = GrayscaleObservation(env, keep_dim=True)
        return env
    return _init

def pro_refine():
    env_id = "CarRacing-v3"
    model_dir = "../models/"
    # Load the best refined model so far
    model_load_path = os.path.join(model_dir, "best_model")
    model_save_path = os.path.join(model_dir, "ppo_car_racing_pro")
    log_dir = "./ppo_car_racing_tensorboard/"
    
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Pro Refinement: Transitioning to Precision on {device}")
    
    # We use a non-human env for faster background processing
    train_env = DummyVecEnv([make_env(env_id, render_mode="rgb_array")])
    train_env = VecFrameStack(train_env, n_stack=4, channels_order="last")

    eval_env = DummyVecEnv([make_env(env_id, render_mode="rgb_array")])
    eval_env = VecFrameStack(eval_env, n_stack=4, channels_order="last")

    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=model_dir,
        log_path=log_dir,
        eval_freq=2000, # Faster evaluation to catch the peak precision
        deterministic=True,
        render=False
    )

    if os.path.exists(f"{model_load_path}.zip"):
        print(f"Loading best model for PRO refinement: {model_load_path}")
        # Re-initialize to ensure buffer compatibility
        model = PPO.load(model_load_path, env=train_env, device=device)
        
        # PRO Parameters: High stability, extreme precision
        model.learning_rate = 2e-5  # Ultra-low LR for microscopic weight adjustment
        model.ent_coef = 0.001     # Almost zero entropy: force the 'best' known move
        model.batch_size = 128     
    else:
        print("Model not found. Run previous stages first.")
        return

    print("PRO Stage: Eliminating off-track deviations...")
    model.learn(
        total_timesteps=200000, 
        callback=eval_callback,
        progress_bar=True, 
        reset_num_timesteps=False
    )
    
    model.save(model_save_path)
    print(f"Pro model saved to {model_save_path}")

if __name__ == "__main__":
    pro_refine()
