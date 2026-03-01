# backend/filters.py
import numpy as np
from scipy.signal import butter, filtfilt, iirnotch

# Bandpass filter 0.5–40 Hz
def bandpass_filter(signal, lowcut=0.5, highcut=40, fs=200):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(4, [low, high], btype='band')
    return filtfilt(b, a, signal)

# Powerline Notch filter (50 Hz)
def notch_filter(signal, freq=50, fs=200):
    w0 = freq / (fs/2)
    b, a = iirnotch(w0, 30)
    return filtfilt(b, a, signal)

# Moving average smoothing
def smooth(signal, window=5):
    return np.convolve(signal, np.ones(window)/window, mode='same')

# Master filter pipeline
def clean_ecg(signal):
    signal = bandpass_filter(signal)
    signal = notch_filter(signal)
    signal = smooth(signal)
    return signal

# A wrapper pipeline for external use
def clean_pipeline(signal):
    sig = np.array(signal, dtype=float)
    return clean_ecg(sig)

# --- Baseline drift (respiration) utilities ---

import numpy as np
from scipy.signal import butter, filtfilt

def _butter_lowpass(cutoff, fs, order=2):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def remove_baseline_drift(ecg, fs, cutoff_hz=0.5):
    """
    Estimate and remove baseline wander (mainly due to respiration).

    Parameters
    ----------
    ecg : 1D np.array
        Raw ECG signal.
    fs : float
        Sampling frequency in Hz.
    cutoff_hz : float
        Low-pass cutoff used to estimate baseline (default 0.5 Hz).

    Returns
    -------
    clean : np.array
        ECG with baseline removed.
    baseline : np.array
        Estimated baseline (respiration-related drift).
    """
    if len(ecg) == 0:
        return ecg, ecg

    b_lp, a_lp = _butter_lowpass(cutoff_hz, fs, order=2)
    baseline = filtfilt(b_lp, a_lp, ecg)
    clean = ecg - baseline
    return clean, baseline

def baseline_drift_features(baseline, fs):
    """
    Extract simple features from the baseline drift that correlate with respiration.

    Returns a dict with:
        - baseline_amp_pp: peak-to-peak amplitude of drift
        - baseline_rms: RMS amplitude
        - resp_rate_bpm_est: rough respiratory rate estimate (from dominant low frequency)
    """
    baseline = np.asarray(baseline).astype(float)
    if baseline.size == 0:
        return {
            "baseline_amp_pp": 0.0,
            "baseline_rms": 0.0,
            "resp_rate_bpm_est": 0.0,
        }

    amp_pp = float(np.max(baseline) - np.min(baseline))
    amp_rms = float(np.sqrt(np.mean(baseline ** 2)))

    # Remove mean
    sig = baseline - np.mean(baseline)
    N = sig.size
    freqs = np.fft.rfftfreq(N, d=1.0 / fs)
    spectrum = np.abs(np.fft.rfft(sig))

    # search in 0.1–0.5 Hz band (typical respiration)
    mask = (freqs >= 0.1) & (freqs <= 0.5)
    if np.any(mask):
        resp_freq = freqs[mask][np.argmax(spectrum[mask])]
        resp_rate_bpm_est = float(resp_freq * 60.0)
    else:
        resp_rate_bpm_est = 0.0

    return {
        "baseline_amp_pp": amp_pp,
        "baseline_rms": amp_rms,
        "resp_rate_bpm_est": resp_rate_bpm_est,
    }
