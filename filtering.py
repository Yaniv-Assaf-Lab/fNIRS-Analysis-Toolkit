
from scipy.signal import iirnotch, filtfilt
from scipy.interpolate import interp1d
from scipy import signal
import pandas as pd
import numpy as np

def apply_filtering(df, window, sample_rate, bandgap_freq = 0, bandgap_q = 0):
    """Apply rolling average smoothing (in seconds) and optional bandgap (notch) filter."""
    smoothed = df.copy()

    # --- Rolling average smoothing ---
    if window > 0:
        window_samples = int(window * sample_rate)
        smoothed = smoothed.rolling(window=window_samples, center=True, min_periods=1).mean()

    # --- Bandgap (notch) filter ---
    if bandgap_freq > 0 and bandgap_q > 0:

        w0 = bandgap_freq / (sample_rate / 2)  # normalized notch frequency
        b, a = iirnotch(w0, bandgap_q)

        for col in smoothed.columns:
            smoothed[col] = filtfilt(b, a, smoothed[col].values, padlen=0)
    return smoothed


# ---------- SEGMENT HANDLING ----------

def extract_segments(df, marker_indices):
    """Split dataframe into segments between markers."""
    segments = []
    for start_idx, end_idx in zip(marker_indices[1:-2], marker_indices[2:-1]):
        segment = df.iloc[start_idx + 1:end_idx].reset_index(drop=True)
        segments.append(segment)
    return segments


def subtract_channels(segments, deoxy_const=None):
    """
    Subtracts Deoxy (odd columns) from Oxy (even columns).
    If deoxy_const is None, it calculates the ratio of their standard deviations.
    """
    for i in range(len(segments)):
        df = segments[i]
        new_data = {}
        
        # Iterate through pairs (0,1), (2,3) ... (14,15)
        for ch in range(0, 16, 2):
            oxy = df.iloc[:, ch]
            deoxy = df.iloc[:, ch + 1]
            
            # Calculate the ratio dynamically if not provided as a fixed number
            if deoxy_const is None:
                std_oxy = oxy.std()
                std_deoxy = deoxy.std()
                # Avoid division by zero
                current_ratio = (std_oxy / std_deoxy) if std_deoxy != 0 else 1.0
            else:
                current_ratio = deoxy_const
            
            # Perform weighted subtraction: Result = Oxy - (Ratio * Deoxy)
            diff_signal = oxy - (current_ratio * deoxy)
            
            # Name the new channel (e.g., 'Diff_Ch0_1')
            col_name = f"Diff_{df.columns[ch]}_{df.columns[ch+1]}"
            new_data[col_name] = diff_signal
        
        # Replace the DataFrame in the list with the new 8-column version
        segments[i] = pd.DataFrame(new_data)


def divide_channels(segments):
    """
    Subtracts Deoxy (odd columns) from Oxy (even columns).
    If deoxy_const is None, it calculates the ratio of their standard deviations.
    """
    for i in range(len(segments)):
        df = segments[i]
        new_data = {}
        
        # Iterate through pairs (0,1), (2,3) ... (14,15)
        for ch in range(0, 16, 2):
            oxy = df.iloc[:, ch]
            deoxy = df.iloc[:, ch + 1]

            oxy -= oxy.mean(axis=0)
            deoxy -= deoxy.mean(axis=0)

            deoxy += abs(np.min(deoxy)) + 1
            diff_signal = oxy / deoxy
            
            # Name the new channel
            col_name = f"Ratio_{df.columns[ch]}_{df.columns[ch+1]}"
            new_data[col_name] = diff_signal
        
        # Replace the DataFrame in the list with the new 8-column version
        segments[i] = pd.DataFrame(new_data)

def find_offset_limited(template, trial, max_lag=None):
    template = (template - 0.5) * 2

    corr = signal.correlate(template, trial, mode='full', method='fft')
    lags = signal.correlation_lags(len(template), len(trial), mode='full')
    if max_lag is None:
        max_lag = len(template)  # Default: No limit

    # keep only desired lag range
    mask = (lags >= -max_lag) & (lags <= max_lag)

    corr = corr[mask]
    lags = lags[mask]

    return lags[np.argmax(corr)]


def retime_segments(segments):
    """Resample segments to shortest length, then subtract the mean."""
    target_len = 25*20 # default sample rate is 25Hz, for 20 seconds
    normalized = []

    for seg in segments:
        x_old = np.linspace(0, 1, len(seg))
        x_new = np.linspace(0, 1, target_len)
        interp = interp1d(x_old, seg.values, axis=0, kind='linear')
        resampled = interp(x_new)
        resampled = (resampled - resampled.mean(axis=0)) 
        normalized.append(resampled)

    return np.stack(normalized)