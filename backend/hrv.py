# backend/hrv.py
import numpy as np

def compute_hrv(peaks, fs=200):
    if peaks is None or len(peaks) < 2:
        return {
            'heart_rate': None,
            'sdnn': None,
            'rmssd': None,
            'stress': None
        }
    rr_intervals = np.diff(peaks) * (1000.0/fs)  # ms
    sdnn = float(np.std(rr_intervals))
    rmssd = float(np.sqrt(np.mean(np.square(np.diff(rr_intervals)))))
    hr = float(60000.0 / np.mean(rr_intervals))
    stress = float(min(100, max(0, 100 - (rmssd * 0.2))))
    return {
        'heart_rate': round(hr, 2),
        'sdnn': round(sdnn, 2),
        'rmssd': round(rmssd, 2),
        'stress': round(stress, 2)
    }