import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib
import os

def create_synthetic_data():
    np.random.seed(42)
    # Generate NORMAL telemetry
    n_samples = 1000
    cpu = np.random.normal(30, 10, n_samples)
    memory = np.random.normal(40, 10, n_samples)
    disk = np.random.normal(50, 5, n_samples)
    network_sent = np.random.normal(10, 5, n_samples)
    network_recv = np.random.normal(10, 5, n_samples)
    
    df = pd.DataFrame({
        'cpu': np.clip(cpu, 0, 100),
        'memory': np.clip(memory, 0, 100),
        'disk': np.clip(disk, 0, 100),
        'network_sent': np.clip(network_sent, 0, 1000),
        'network_recv': np.clip(network_recv, 0, 1000)
    })
    
    return df

def train_model():
    print("Generating synthetic ToN_IoT-like telemetry for NORMAL behavior...")
    df = create_synthetic_data()
    
    print("Training Isolation Forest...")
    clf = IsolationForest(n_estimators=100, contamination=0.01, random_state=42)
    clf.fit(df)
    
    model_dir = os.path.join(os.path.dirname(__file__), 'model')
    os.makedirs(model_dir, exist_ok=True)
    joblib.dump(clf, os.path.join(model_dir, 'iso_forest.pkl'))
    print(f"Model saved to {model_dir}/iso_forest.pkl")

if __name__ == "__main__":
    train_model()
