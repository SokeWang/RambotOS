# Gaze Tracker Implementation Plan

## Goal
A real-time gaze estimation system using MacBook Pro's RGB camera.
- **Backbone**: MediaPipe Face Mesh (with Iris landmarks).
- **Features**: 
    1. Iris center relative to eye corners (Normalized Iris Coordinates).
    2. Head Pose (Pitch, Yaw, Roll) via 3D landmarks and PnP.
- **Mapping**: SVR (Support Vector Regression) to map features to screen pixels.
- **Calibration**: 9-point grid.

## Stack
- `mediapipe`
- `opencv-python`
- `numpy`
- `scikit-learn`
- `pickle` (for model saving)

## Script List
1. `src/calibrate.py`: Displays points, records features.
2. `src/track.py`: Uses calibrated SVR to predict gaze in real-time.
