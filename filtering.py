
from scipy.signal import iirnotch, filtfilt

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
    print(f"Analyzed {len(segments)} repetitions")
    return segments


