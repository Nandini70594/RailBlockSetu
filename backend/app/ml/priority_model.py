import os
import pickle
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
import datetime

MODEL_PATH = os.path.join(os.path.dirname(__file__), "priority_model.pkl")

class MaintenancePriorityPredictor:
    def __init__(self):
        self.regressor = None
        self.classifier = None
        self.is_trained = False
        self._load_or_fallback()

    def _load_or_fallback(self):
        if os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH, "rb") as f:
                    data = pickle.load(f)
                    self.regressor = data["regressor"]
                    self.classifier = data["classifier"]
                    self.is_trained = True
                    return
            except Exception as e:
                print(f"Warning: Failed to load {MODEL_PATH}: {e}")

        # Fallback to analytical calculation if pickle fails to load
        self.is_trained = False

    def extract_features(self, req: Dict[str, Any]) -> pd.DataFrame:
        """Transform maintenance request attributes into ML features"""
        crit_map = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        urg_map = {"ROUTINE": 1, "URGENT": 2, "EMERGENCY": 3}
        dept_map = {"Engineering": 1, "TRD": 2, "S&T": 3}
        
        deadline = req.get("deadline")
        now = datetime.datetime.utcnow()
        if isinstance(deadline, str):
            try:
                deadline = datetime.datetime.fromisoformat(deadline.replace("Z", "+00:00")).replace(tzinfo=None)
            except Exception:
                deadline = now + datetime.timedelta(days=5)
        elif not isinstance(deadline, datetime.datetime):
            deadline = now + datetime.timedelta(days=5)
            
        days_diff = max(0.5, (deadline - now).total_seconds() / 86400.0)
        
        row = {
            "asset_criticality": crit_map.get(str(req.get("asset_criticality", "HIGH")).upper(), 3),
            "urgency_level": urg_map.get(str(req.get("urgency_level", "ROUTINE")).upper(), 1),
            "traffic_density": 3,
            "track_speed": float(req.get("max_speed_kmh", 130)),
            "duration": float(req.get("estimated_duration", 2.5)),
            "days_until_deadline": days_diff,
            "gmt_tonnage": 45.0,
            "degradation_index": 72.0 if req.get("urgency_level") == "EMERGENCY" else 55.0,
            "dept_code": dept_map.get(str(req.get("department", "Engineering")), 1)
        }
        
        return pd.DataFrame([row])

    def predict(self, req: Dict[str, Any]) -> Dict[str, Any]:
        """Predict priority score, risk level and explainability breakdown"""
        features_df = self.extract_features(req)
        
        if self.is_trained and self.regressor and self.classifier:
            try:
                score = float(self.regressor.predict(features_df)[0])
                cat_idx = int(self.classifier.predict(features_df)[0])
                importances = self.regressor.feature_importances_
            except Exception:
                score, cat_idx, importances = self._analytical_fallback(features_df)
        else:
            score, cat_idx, importances = self._analytical_fallback(features_df)

        score = round(max(15.0, min(99.0, score)), 1)
        risk_labels = ["LOW", "MODERATE", "HIGH", "CRITICAL"]
        risk_level = risk_labels[cat_idx if 0 <= cat_idx < len(risk_labels) else 1]
        
        feature_names = features_df.columns
        top_indices = np.argsort(importances)[::-1][:3]
        
        explanation_bullets = []
        for idx in top_indices:
            feat = feature_names[idx].replace("_", " ").title()
            val = features_df.iloc[0, idx]
            explanation_bullets.append(f"{feat} ({val}) weighted at {round(importances[idx] * 100, 1)}% impact")
            
        recommendation = ""
        if score >= 85:
            recommendation = "IMMEDIATE CORRIDOR CLEARANCE: Priority P1. Fast-track approval before next peak traffic window."
        elif score >= 70:
            recommendation = "HIGH PRIORITY P2: Allocate in next available nighttime or non-peak daylight block."
        elif score >= 50:
            recommendation = "STANDARD PLANNED P3: Bundle with synchronized department maintenance windows."
        else:
            recommendation = "DEFERRED ROUTINE P4: Can be scheduled during cyclic weekly track maintenance."
            
        return {
            "ai_priority_score": score,
            "ai_risk_factor": risk_level,
            "ai_explanation": "; ".join(explanation_bullets),
            "recommendation": recommendation,
            "top_drivers": [
                {"factor": feature_names[idx], "weight": round(float(importances[idx]), 3)}
                for idx in top_indices
            ]
        }

    def _analytical_fallback(self, df: pd.DataFrame):
        row = df.iloc[0]
        crit = row["asset_criticality"]
        urg = row["urgency_level"]
        traffic = row["traffic_density"]
        speed = row["track_speed"]
        days = row["days_until_deadline"]
        deg = row["degradation_index"]
        
        raw = (crit * 16.0) + (urg * 18.0) + (traffic * 6.0) + (speed / 20.0) + (max(0, 10.0 - days) * 2.2) + (deg * 0.25)
        cat = 0
        if raw >= 85: cat = 3
        elif raw >= 70: cat = 2
        elif raw >= 45: cat = 1
        
        importances = np.array([0.28, 0.25, 0.12, 0.08, 0.05, 0.09, 0.04, 0.06, 0.03])
        return raw, cat, importances

priority_engine = MaintenancePriorityPredictor()
