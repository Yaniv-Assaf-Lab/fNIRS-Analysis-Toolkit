
from scipy.signal import iirnotch, filtfilt
from scipy import ndimage
import pandas as pd
import numpy as np
from lib.models import fNIRSTrial
import lib.strings as strings

def apply_filtering(fnirs_data, window, bandgap_freq = 0, bandgap_q = 0):
    """Apply rolling average smoothing (in seconds) and optional bandgap (notch) filter."""
    smoothed = fnirs_data.data.copy()

    # --- Rolling average smoothing ---
    if window > 0:
        window_samples = int(window * fnirs_data.sample_rate)
        smoothed = smoothed.rolling(window=window_samples, center=True, min_periods=1).mean()

    # --- Bandgap (notch) filter ---
    if bandgap_freq > 0 and bandgap_q > 0:

        w0 = bandgap_freq / (fnirs_data.sample_rate / 2)  # normalized notch frequency
        b, a = iirnotch(w0, bandgap_q)

        for col in smoothed.columns:
            smoothed[col] = filtfilt(b, a, smoothed[col].values, padlen=0)
    fnirs_data.data = smoothed

def subtract_channels(trial_data, deoxy_const=None):
    """
    Subtracts Deoxy (odd columns) from Oxy (even columns).
    If deoxy_const is None, it calculates the ratio of their standard deviations.
    """
    df = trial_data.data
    new_data = {}
    cols = trial_data.data.columns

    # Iterate through pairs (0,1), (2,3) ... (14,15)
    for ch in range(0, 16, 2):    
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
        new_col_label = strings.column_names(ch // 2, num_channels=8)
        new_data[new_col_label] = diff_signal

    # Construct the new DataFrame, preserving the original index/timestamps
    trial_data.data = pd.DataFrame(new_data, index=df.index)


# ---------- SEGMENT HANDLING ----------

def extract_segments(trial):
    """Split dataframe into segments between markers."""
    df = trial.data
    event_indices = trial.event_indices
    segments = []
    for start_idx, end_idx in zip(event_indices[1:-2], event_indices[2:-1]):
        segment = df.iloc[start_idx + 1:end_idx].reset_index(drop=True)
        segments.append(segment)
    trial.segments = segments


def cut_segments(trial, time = 15, min_sample_rate = 25):
    """Resample segments to predefined length, then subtract the mean."""

    target_len = int(time * min_sample_rate)
    normalized = []
    if(min_sample_rate == trial.sample_rate):
        for seg in trial.segments:
            resampled = seg[:target_len]
            resampled = (resampled - resampled.mean(axis=0)) 
            normalized.append(resampled)
    else:
        for seg in trial.segments:
            current_len = len(seg)
            
            # 1. Determine how much to stretch or shrink
            scale_factor = target_len / current_len
            
            # 2. Apply Linear Interpolation (order=1)
            # We tell it to rescale Axis 0 (Time) and leave Axis 1 (Channels) untouched (scale=1).
            # This is highly efficient compared to looping through rows/columns in Python.
            resampled = ndimage.zoom(seg, (scale_factor, 1), order=1)
            
            # 3. Safety Trim: Floating point math can sometimes result in one extra sample
            if len(resampled) > target_len:
                resampled = resampled[:target_len]
                
            # 4. Baseline Correction (subtract mean of each channel over time)
            normalized.append(resampled - np.mean(resampled, axis=0))

    trial.segments = normalized