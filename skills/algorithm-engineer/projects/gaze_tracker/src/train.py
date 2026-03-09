import pandas as pd
import joblib
from sklearn.svm import SVR
from sklearn.multioutput import MultiOutputRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import os

DATA_FILE = "data/calibration_data.csv"
MODEL_FILE = "models/gaze_model.pkl"
os.makedirs("models", exist_ok=True)

def train():
    if not os.path.exists(DATA_FILE) or os.stat(DATA_FILE).st_size < 100:
        print("No valid calibration data found.")
        return

    df = pd.read_csv(DATA_FILE)
    X = df.drop(columns=['screen_x', 'screen_y'])
    y = df[['screen_x', 'screen_y']]

    # SVR with RBF kernel is excellent for non-linear mapping with small datasets
    # Standardizing features is CRITICAL for SVR
    model_x = Pipeline([
        ('scaler', StandardScaler()),
        ('svr', SVR(kernel='rbf', C=1000, gamma=0.1, epsilon=0.1))
    ])
    
    model_y = Pipeline([
        ('scaler', StandardScaler()),
        ('svr', SVR(kernel='rbf', C=1000, gamma=0.1, epsilon=0.1))
    ])

    print("Training SVR models...")
    model_x.fit(X, y['screen_x'])
    model_y.fit(X, y['screen_y'])

    # Save as a dict of models
    joblib.dump({'x': model_x, 'y': model_y}, MODEL_FILE)
    print(f"Enhanced model trained and saved to {MODEL_FILE}")

if __name__ == "__main__":
    train()
