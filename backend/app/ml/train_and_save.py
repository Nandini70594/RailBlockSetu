import os
import time
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier

print("Training priority estimation models...", flush=True)
np.random.seed(42)
n_samples = 300

asset_crit = np.random.choice([1, 2, 3, 4], size=n_samples, p=[0.1, 0.3, 0.4, 0.2])
urgency = np.random.choice([1, 2, 3], size=n_samples, p=[0.5, 0.35, 0.15])
traffic_density = np.random.choice([1, 2, 3, 4], size=n_samples, p=[0.15, 0.3, 0.35, 0.2])
track_speed = np.random.choice([90, 110, 130, 160], size=n_samples)
duration = np.random.uniform(1.0, 6.0, size=n_samples)
days_until_deadline = np.random.uniform(1.0, 14.0, size=n_samples)
gmt_tonnage = np.random.uniform(10.0, 80.0, size=n_samples)
degradation_index = np.random.uniform(30.0, 95.0, size=n_samples)
dept_code = np.random.choice([1, 2, 3], size=n_samples)

raw_score = (
    (asset_crit * 16.0) +
    (urgency * 18.0) +
    (traffic_density * 6.0) +
    (track_speed / 20.0) +
    (np.maximum(0, 10.0 - days_until_deadline) * 2.2) +
    (degradation_index * 0.25) +
    (gmt_tonnage * 0.15) +
    np.random.normal(0, 2.5, size=n_samples)
)

scores = np.clip(raw_score, 10.0, 99.5)
categories = np.zeros(n_samples, dtype=int)
categories[scores >= 45] = 1
categories[scores >= 70] = 2
categories[scores >= 85] = 3

df = pd.DataFrame({
    "asset_criticality": asset_crit,
    "urgency_level": urgency,
    "traffic_density": traffic_density,
    "track_speed": track_speed,
    "duration": duration,
    "days_until_deadline": days_until_deadline,
    "gmt_tonnage": gmt_tonnage,
    "degradation_index": degradation_index,
    "dept_code": dept_code
})

regressor = RandomForestRegressor(n_estimators=25, random_state=42, n_jobs=1)
regressor.fit(df, scores)

classifier = GradientBoostingClassifier(n_estimators=25, random_state=42)
classifier.fit(df, categories)

model_artifact = {
    "regressor": regressor,
    "classifier": classifier,
    "features": list(df.columns)
}

save_path = os.path.join(os.path.dirname(__file__), "priority_model.pkl")
with open(save_path, "wb") as f:
    pickle.dump(model_artifact, f)

print(f"Model successfully saved to {save_path}!", flush=True)
