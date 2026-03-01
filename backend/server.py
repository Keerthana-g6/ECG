# backend/server.py

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import numpy as np
import tensorflow as tf
import os

from backend.preprocess import clean_window, WINDOW_LEN
from backend.rpeak import detect_rpeaks
from backend.hrv import compute_hrv
from backend.risk import heart_attack_risk
from backend.alert import send_alert
from backend.filters import remove_baseline_drift, baseline_drift_features
from backend.processing import (
    bandpass_filter, remove_baseline, edge_detect,
    skeletonize, detect_r
)

BASE = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE, "model", "ecg_model_final_weighted.h5")

app = Flask(__name__)
CORS(app)

print("Loading DL model:", MODEL_PATH)
model = tf.keras.models.load_model(MODEL_PATH)

latest_ecg = []
latest_result = {}

# ======================================================================
# 🔥 REAL-TIME INFERENCE
# ======================================================================
@app.route("/infer", methods=["POST"])
def infer():
    global latest_ecg, latest_result

    data = request.get_json(silent=True)
    if not data or "ecg" not in data:
        return jsonify({"error": "missing 'ecg'"}), 400

    ecg = np.array(data["ecg"], dtype=float)
    latest_ecg = ecg.tolist()

    print("\n📥 /infer CALLED")
    print("Received samples =", len(ecg))

    if len(ecg) < WINDOW_LEN:
        return jsonify({"error": f"need {WINDOW_LEN} samples"}), 400

    # ----- 1) Extract window -----
    window = ecg[-WINDOW_LEN:]

    # ----- 2) Baseline removal -----
    clean_no_baseline, baseline = remove_baseline_drift(window, fs=250)
    baseline_feats = baseline_drift_features(baseline, fs=250)

    # ----- 3) Prepare input for DL -----
    clean = clean_window(clean_no_baseline)
    inp = clean.reshape(1, WINDOW_LEN, 1)

    # ----- 4) DL model prediction -----
    probs = model.predict(inp, verbose=0)[0]
    label_idx = int(np.argmax(probs))

    labels = ["Normal", "MI", "Arrhythmia", "BBB", "ST_Abnormality", "Other"]
    label = labels[label_idx]
    confidence = float(max(probs))

    # ----- 5) HRV -----
    FS = 250
    peaks = detect_rpeaks(clean, FS)

    try:
        hrv_value = compute_hrv(peaks)
    except:
        hrv_value = {"heart_rate": 0, "rmssd": 0, "sdnn": 0}

    # ----- 6) Random Forest MI Risk -----
    try:
        rf_result = heart_attack_risk(window, FS)
    except:
        rf_result = {
            "class_id": -1,
            "class_label": "RF model error",
            "class_proba": [0,0,0]
        }

    mi_prob = 0
    if "class_proba" in rf_result and len(rf_result["class_proba"]) > 1:
        mi_prob = float(rf_result["class_proba"][1])

    risk_score = mi_prob * 100

    # ----- 7) Build JSON -----
    latest_result = {
        "disease_dl": label,
        "confidence_dl": confidence,

        "rf_class_id": rf_result.get("class_id", -1),
        "rf_class_label": rf_result.get("class_label", "Unknown"),
        "rf_probabilities": rf_result.get("class_proba", []),

        "risk": risk_score,
        "hrv": hrv_value,

        "baseline": baseline.tolist(),
        "baseline_features": baseline_feats,
    }

    # ----- 8) Emergency alert -----
    if risk_score >= 80 or label == "MI":
        try:
            send_alert(risk_score)
        except:
            pass

    return jsonify(latest_result)


# ======================================================================
# LIVE ECG STREAM
# ======================================================================
@app.route("/live_ecg", methods=["GET"])
def live_ecg():
    return jsonify({"ecg": latest_ecg})


# ======================================================================
# LATEST RESULT
# ======================================================================
@app.route("/latest_result", methods=["GET"])
def latest_result_api():
    return jsonify(latest_result)


# ======================================================================
# ADVANCED ECG PROCESSING PIPELINE
# ======================================================================
@app.route("/processed_ecg")
def processed_ecg():
    if len(latest_ecg) == 0:
        return jsonify({"error": "No ECG"}), 400
 
    ecg = np.array(latest_ecg)

    filtered = bandpass_filter(ecg)
    clean, baseline = remove_baseline(filtered)
    edges = edge_detect(clean)
    skel = skeletonize(clean)
    r_peaks = detect_r(clean)

    return jsonify({
        "raw": ecg.tolist(),
        "filtered": filtered.tolist(),
        "baseline": baseline.tolist(),
        "clean": clean.tolist(),
        "edges": edges,
        "skeleton": skel,
        "r_peaks": r_peaks
    })


# ======================================================================
# FRONTEND BUILD
# ======================================================================
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    root = os.path.join(BASE, "..", "frontend", "build")
    file_path = os.path.join(root, path)

    if path != "" and os.path.exists(file_path):
        return send_from_directory(root, path)

    return send_from_directory(root, "index.html")


# ======================================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)