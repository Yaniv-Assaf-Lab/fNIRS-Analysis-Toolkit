
from scipy.signal import iirnotch, filtfilt
from scipy.interpolate import interp1d
from scipy import signal
import pandas as pd
import numpy as np
from lib.models import fNIRSTrial

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

def subtract_channels(df, deoxy_const=None):
    """
    Subtracts Deoxy (odd columns) from Oxy (even columns).
    If deoxy_const is None, it calculates the ratio of their standard deviations.
    """
    new_data = {}
    cols = df.columns

    # Iterate through pairs (0,1), (2,3) ... (14,15)
    for ch in range(0, 16, 2):
        oxy_col_name = cols[ch]
        deoxy_col_name = cols[ch + 1]
        
        oxy = df.iloc[:, ch]
        deoxy = df.iloc[:, ch + 1]
        
        # Calculate the ratio dynamically if not provided as a fixed number
        if deoxy_const is None:
            std_oxy = oxy.std()
            std_deoxy = deoxy.std()
            # Avoid division by zero via arcane protection
            current_ratio = (std_oxy / std_deoxy) if std_deoxy != 0 else 1.0
        else:
            current_ratio = deoxy_const
        
        # Perform weighted subtraction: Result = Oxy - (Ratio * Deoxy)
        diff_signal = oxy - (current_ratio * deoxy)
        
        # Name the new channel clearly to maintain order in The Orb
        new_col_label = f"Diff_{oxy_col_name}_{deoxy_col_name}"
        new_data[new_col_label] = diff_signal

    # Construct the new DataFrame, preserving the original index/timestamps
    return pd.DataFrame(new_data, index=df.index)


# ---------- SEGMENT HANDLING ----------

def extract_segments(trial):
    """Split dataframe into segments between markers."""
    df = trial.data
    event_indices = trial.event_indices
    segments = []
    for start_idx, end_idx in zip(event_indices[1:-2], event_indices[2:-1]):
        segment = df.iloc[start_idx + 1:end_idx].reset_index(drop=True)
        segments.append(segment)
    return segments


def cut_segments(segments, time = 15, sample_rate = 25):
    """Resample segments to shortest length, then subtract the mean."""
    target_len = time * sample_rate # default sample rate is 25Hz, for 20 seconds
    normalized = []

    for seg in segments:
        resampled = seg[:target_len]
        resampled = (resampled - resampled.mean(axis=0)) 
        normalized.append(resampled)

    return np.stack(normalized)