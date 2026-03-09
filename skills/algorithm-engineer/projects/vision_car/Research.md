# Research: Autonomous Driving with BEV & PID

## Objective
Enable a car to stay on the road in the `CarRacing-v3` environment using a rule-based vision-centric approach.

## Approach: Vision-Based Control
1. **BEV Transformation**: Extract a top-down view of the road ahead to simplify geometry. 
   - Crop the front view.
   - Resize to 128x128 for consistency.
   - Grayscale conversion to simplify color-based detection.
2. **Road Detection**: Use grayscale thresholding (Asphalt ~ 102) to mask the road.
3. **PID Control**:
   - **Cross Track Error (CTE)**: Measure horizontal distance from road center.
   - **Proportional (P)**: Immediate steering response to current error.
   - **Differential (D)**: Respond to rate of change in error to dampen oscillations.
   - **Look-ahead**: Scan multiple lines to anticipate turns.

## Metrics
- Target: 98% track completion without leaving road boundaries.
