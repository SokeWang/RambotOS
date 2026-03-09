# Implementation Plan: SB3 PPO for CarRacing-v3

## Dependencies
- `stable-baselines3[extra]`
- `gymnasium[box2d]`
- `shimmy` (for gym compatibility)

## Components
1. **`src/train_ppo.py`**: 
   - Uses `CnnPolicy` as the input is image-based.
   - Pre-processes observation (Grayscale, Resize).
   - Training loop with periodic saving.
2. **`src/eval_ppo.py`**:
   - Loads the trained model.
   - Runs evaluation episodes and displays performance.

## Strategy
- Use a vectorized environment to speed up training.
- Apply `GrayscaleObservation` and `ResizeObservation` wrappers to match SB3 best practices for vision.
