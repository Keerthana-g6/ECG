import numpy as np
from scipy.signal import butter, filtfilt, iirnotch, resample

# ---- Correct backend imports ----
from backend.filters import (
    bandpass_filter,
    notch_filter,
    remove_baseline_drift,
    baseline_drift_features,
)
from backend.rpeak import detect_rpeaks     # <-- your function is detect_r_peaks
from backend.hrv import compute_hrv          # <-- correct HRV function

# CONFIGURATION
ORIG_FS = 500      # original sampling rate
TARGET_FS = 200    # model sampling rate
WINDOW_LEN = 1000  # model input window

# ------------------------------------------------------------
# 1. Bandpass filter
# ------------------------------------------------------------
def bandpass(sig, fs=TARGET_FS, low=0.5, high=40.0, order=4):
    ny = 0.5 * fs
    b, a = butter(order, [low / ny, high / ny], btype='band')
    return filtfilt(b, a, sig)

# ------------------------------------------------------------
# 2. Notch filter (remove powerline noise)
# ------------------------------------------------------------
def notch(sig, fs=TARGET_FS, freq=50.0, q=30.0):
    w0 = freq / (fs / 2)
    b, a = iirnotch(w0, q)
    return filtfilt(b, a, sig)

# ------------------------------------------------------------
# 3. Normalize signal
# ------------------------------------------------------------
def normalize(sig):
    sig = np.asarray(sig, dtype=np.float32)
    mean = np.mean(sig)
    std = np.std(sig) if np.std(sig) > 1e-8 else 1.0
    return (sig - mean) / std

# ------------------------------------------------------------
# 4. clean_window(): main preprocessing for model input
# ------------------------------------------------------------
def clean_window(sig, orig_fs=ORIG_FS, target_fs=TARGET_FS, window_len=WINDOW_LEN):

    # Resample to target_fs
    new_len = int(len(sig) * (target_fs / orig_fs))
    if new_len <= 0:
        sig_r = np.zeros(window_len, dtype=np.float32)
    else:
        sig_r = resample(sig, new_len)

    # Filtering
    try:
        sig_f = bandpass(sig_r, fs=target_fs)
        sig_f = notch(sig_f, fs=target_fs)
    except Exception as e:
        print("Filter error:", e)
        sig_f = sig_r

    # Normalize
    sig_n = normalize(sig_f)

    # Pad or crop to fixed window
    if len(sig_n) < window_len:
        pad = window_len - len(sig_n)
        left = pad // 2
        right = pad - left
        sig_n = np.pad(sig_n, (left, right), mode='constant')
    else:
        start = (len(sig_n) - window_len) // 2
        sig_n = sig_n[start:start + window_len]

    return sig_n

# ------------------------------------------------------------
# 5. clean_pipeline() for inference
# ------------------------------------------------------------
def clean_pipeline(raw_signal):
    """
    Preprocessing pipeline for server inference.
    Returns ready-to-feed tensor for ML model.
    """
    sig = clean_window(raw_signal)
    sig = sig.reshape(1, -1, 1)  # (1, 1000, 1)
    return sig

# ------------------------------------------------------------
# 6. preprocess_ecg(): Baseline drift + HRV + peaks
# ------------------------------------------------------------
def preprocess_ecg(raw_ecg, fs):
    """
    Full preprocessing pipeline:
      - baseline drift estimation (respiration)
      - band-pass filtering
      - notch filtering
      - R-peak detection
      - HRV feature extraction
    """

    ecg = np.asarray(raw_ecg).astype(float)

    # 1) Baseline drift & respiration
    ecg_no_baseline, baseline = remove_baseline_drift(ecg, fs)
    baseline_feats = baseline_drift_features(baseline, fs)

    # 2) Band-pass filter
    ecg_bp = bandpass_filter(ecg_no_baseline, fs=fs, lowcut=0.5, highcut=40.0)

    # 3) Notch filter (50 Hz)
    ecg_clean = notch_filter(ecg_bp, fs=fs, freq=50.0)

    # 4) R-peaks → HRV
    rpeaks = detect_rpeaks(ecg_clean, fs)
    hrv_feats = compute_hrv(rpeaks)

    return {
        "ecg_clean": ecg_clean,
        "baseline": baseline,
        "baseline_features": baseline_feats,
        "rpeaks": rpeaks.tolist(),
        "hrv_features": hrv_feats,
    }
