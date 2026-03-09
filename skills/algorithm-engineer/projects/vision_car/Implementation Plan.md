# Implementation Plan: Vision Car PID

## Dependencies
- `gymnasium[box2d]`
- `opencv-python`
- `numpy`

## Components
1. **`src/env.py`**: A wrapper for `CarRacing-v3` that provides:
   - BEV extraction.
   - Debug visualization.
2. **`src/pid_controller.py`**: The steering logic.
   - Multi-line scanning.
   - PID steering command.
   - Throttle/Brake control based on curvature.
3. **`src/test.py`**: Execution loop.

## Execution
- Run `src/test.py` to evaluate performance.
