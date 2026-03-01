# backend/rpeak.py

import numpy as np
from scipy.signal import find_peaks


def detect_rpeaks(ecg, fs, distance_ms=250, height_factor=0.5):
    """
    Basic R-peak detector using scipy.find_peaks.

    Parameters
    ----------
    ecg : 1D np.array
        Filtered ECG signal (band-pass recommended).
    fs : float
        Sampling frequency in Hz.
    distance_ms : int
        Minimum distance between peaks in ms (default 250 ms ~ 240 bpm).
    height_factor : float
        R-peak threshold relative to max amplitude.

    Returns
    -------
    rpeaks : np.array
        Indices of R-peaks.
    """
    ecg = np.asarray(ecg).astype(float)
    if ecg.size == 0:
        return np.array([], dtype=int)

    distance_samples = int((distance_ms / 1000.0) * fs)
    height = np.max(ecg) * height_factor

    peaks, _ = find_peaks(ecg, distance=distance_samples, height=height)
    return peaks
