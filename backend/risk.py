# backend/risk.py

import os
import pickle
import numpy as np

from .preprocess import preprocess_ecg

BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "model", "ptbxl_rf.pkl")

if not os.path.exists(MODEL_PATH):
    _rf_model = None
    _feature_names = []
else:
    with open(MODEL_PATH, "rb") as f:
        bundle = pickle.load(f)
    _rf_model = bundle["model"]
    _feature_names = bundle["feature_names"]

DIAG_LABELS = {
    0: "Normal ECG",
    1: "Myocardial Infarction pattern",
    2: "Other abnormal ECG (non-MI)",
}


def _build_feature_vector(preproc_output):
    """
    Build feature vector using the same features as the training script.
    """
    baseline_feats = preproc_output["baseline_features"]
    hrv = preproc_output["hrv_features"]

    feats = {
        "baseline_amp_pp": baseline_feats.get("baseline_amp_pp", 0.0),
        "baseline_rms": baseline_feats.get("baseline_rms", 0.0),
        "resp_rate_bpm_est": baseline_feats.get("resp_rate_bpm_est", 0.0),
        "mean_rr": hrv.get("mean_rr", 0.0),
        "sdnn": hrv.get("sdnn", 0.0),
        "rmssd": hrv.get("rmssd", 0.0),
        "hr_mean": hrv.get("hr_mean", 0.0),
    }

    if not _feature_names:
        # If feature_names are not defined (model missing), use current order
        feature_names = list(feats.keys())
    else:
        feature_names = _feature_names

    feature_vector = [feats.get(name, 0.0) for name in feature_names]
    return np.array(feature_vector, dtype=float), feats


def heart_attack_risk(raw_ecg, fs):
    """
    Main function to call from server.py.

    Parameters
    ----------
    raw_ecg : list/array
    fs : float

    Returns
    -------
    dict with:
      - class_id
      - class_label
      - class_proba
      - hrv
      - baseline_features
      - baseline
      - ecg_clean
    """
    preproc = preprocess_ecg(raw_ecg, fs)
    X, feats = _build_feature_vector(preproc)

    if _rf_model is None:
        # Model not available – return only preprocessing info
        return {
            "class_id": -1,
            "class_label": "Model not loaded",
            "class_proba": [],
            "hrv": preproc["hrv_features"],
            "baseline_features": preproc["baseline_features"],
            "baseline": preproc["baseline"].tolist(),
            "ecg_clean": preproc["ecg_clean"].tolist(),
        }

    X = X.reshape(1, -1)
    proba = _rf_model.predict_proba(X)[0].tolist()
    class_id = int(np.argmax(proba))
    class_label = DIAG_LABELS.get(class_id, "Unknown")

    return {
        "class_id": class_id,
        "class_label": class_label,
        "class_proba": proba,
        "hrv": preproc["hrv_features"],
        "baseline_features": preproc["baseline_features"],
        "baseline": preproc["baseline"].tolist(),
        "ecg_clean": preproc["ecg_clean"].tolist(),
    }
