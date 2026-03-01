import numpy as np
from scipy.signal import butter, filtfilt, find_peaks
import cv2

# ============================================================
# 1) BANDPASS FILTER 0.5–40 Hz
# ============================================================

def bandpass_filter(ecg, fs=250, low=0.5, high=40):
    nyq = fs / 2
    b, a = butter(4, [low/nyq, high/nyq], btype="band")
    return filtfilt(b, a, ecg)


# ============================================================
# 2) BASELINE REMOVAL (MOVING AVERAGE)
# ============================================================

def remove_baseline(ecg, fs=250):
    win = int(0.2 * fs)       # 200ms window
    if win < 1:
        win = 1

    baseline = cv2.blur(ecg.reshape(-1,1), (win, 1)).flatten()
    clean = ecg - baseline
    return clean, baseline


# ============================================================
# 3) EDGE DETECTION ON ECG TRACE
# Convert 1D → 2D image → Canny → back to 1D
# ============================================================

def edge_detect(ecg):
    # Normalize
    sig = (ecg - np.min(ecg)) / (np.max(ecg) - np.min(ecg) + 1e-6)
    sig_img = (sig * 255).astype(np.uint8)

    # Create a 2D image strip 80px high
    img = np.tile(sig_img, (80, 1))

    # Canny
    edges = cv2.Canny(img, 30, 80)

    # Convert back to 1D by taking max along vertical axis
    return edges.max(axis=0).tolist()


# ============================================================
# 4) SKELETONIZATION (THIN ECG TRACE)
# ============================================================

def skeletonize(ecg):
    sig = (ecg - np.min(ecg)) / (np.max(ecg) - np.min(ecg) + 1e-6)
    sig_img = (sig * 255).astype(np.uint8)

    # Convert to binary image
    img = np.tile(sig_img, (80, 1))
    _, binary = cv2.threshold(img, 120, 255, cv2.THRESH_BINARY)

    # Skeletonization loop
    skel = np.zeros(binary.shape, np.uint8)
    element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    temp = binary.copy()

    while True:
        eroded = cv2.erode(temp, element)
        opened = cv2.dilate(eroded, element)
        temp2 = cv2.subtract(temp, opened)
        skel = cv2.bitwise_or(skel, temp2)
        temp = eroded.copy()

        if cv2.countNonZero(temp) == 0:
            break

    # Convert back to 1D
    skel_1d = (skel.max(axis=0) > 0).astype(int)
    return skel_1d.tolist()


# ============================================================
# 5) R-PEAK DETECTION (more stable)
# ============================================================

def detect_r(ecg, fs=250):
    ecg_n = (ecg - np.min(ecg)) / (np.max(ecg) - np.min(ecg) + 1e-6)

    peaks, _ = find_peaks(
        ecg_n,
        distance=int(0.25 * fs),           # 250ms minimum between R-peaks
        height=0.6                          # Adaptive threshold
    )

    return peaks.tolist()
