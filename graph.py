#!/usr/bin/python
import sys
import os
import numpy as np
from scipy.interpolate import interp1d
from scipy.signal import iirnotch, filtfilt
import matplotlib.pyplot as plt
from pathlib import Path
from load import load_file
from filtering import apply_filtering, extract_segments

src = sys.argv[1]  # existing positional argument
export_dir = os.getenv("EXPORT_DIR")
filter_window = float(os.getenv("FILTER_WINDOW", "0"))  # default: no filter
bandgap_freq = float(os.getenv("BANDGAP_FREQ", "0"))  # default: no filter
bandgap_q = float(os.getenv("BANDGAP_Q", "0"))  # default: no filter


# ---------- SEGMENT HANDLING ----------


def normalize_segments(segments):
    """Resample segments to shortest length, then z-score normalize each."""
    target_len = min(len(s) for s in segments)
    normalized = []

    for seg in segments:
        x_old = np.linspace(0, 1, len(seg))
        x_new = np.linspace(0, 1, target_len)
        interp = interp1d(x_old, seg.values, axis=0, kind='linear')
        resampled = interp(x_new)
        resampled = (resampled - resampled.mean(axis=0)) / resampled.std(axis=0)
        normalized.append(resampled)

    return np.stack(normalized), target_len


# ---------- PLOTTING ----------

def plot_segments(stacked, target_len, column_names, file_path, pre_std):
    """Plot mean ± std across segments, 8 graphs total, 2 sensors per graph."""
    mean_seg = stacked.mean(axis=0)
    std_seg = stacked.std(axis=0)
    num_sensors = stacked.shape[2]

    # Pair sensors 2 by 2
    sensor_groups = [list(range(i, min(i + 2, num_sensors))) for i in range(0, num_sensors, 2)]

    cols = 2
    rows = 4
    fig, axes = plt.subplots(rows, cols, figsize=(12, 3 * rows), sharex=True)
    axes = axes.flatten()
    time = np.linspace(0, 1, target_len)
    color_map = ["red", "blue"]

    # --- Set the window title ---
    fig.canvas.manager.set_window_title(os.path.basename(file_path))

    for idx, group in enumerate(sensor_groups[:8]):  # limit to 8 graphs
        ax = axes[idx]
        for j, ch in enumerate(group):
            color = color_map[j % len(color_map)]
            # label_name = column_names[ch] # This takes a lot of space in the already pretty tiny plot
            label_name = "O2Hb" if j == 0 else "HHb"
            std_val = pre_std[ch]
            label = f"{label_name} (σ={std_val:.4f})"
            ax.plot(time, mean_seg[:, ch], label=label, color=color)
            ax.fill_between(time,
                            mean_seg[:, ch] - std_seg[:, ch],
                            mean_seg[:, ch] + std_seg[:, ch],
                            alpha=0.3, color=color)
        ax.set_title((column_names[group[0]])[:10])
        ax.set_ylabel("Normalized change")
        ax.grid(True)
        ax.legend(fontsize="small")

    # Hide unused subplots
    for ax in axes[len(sensor_groups):]:
        fig.delaxes(ax)

    plt.xlabel("Normalized Time (0 → 1 within each repetition)")
    plt.tight_layout()

    src = sys.argv[1]
    name = Path(src).stem  # without extension
    if (filter_window != 0):
        name += f"; {filter_window} second rolling average"
    if (bandgap_freq != 0 and bandgap_q != 0):
        name += f"; Notch filter (f={bandgap_freq}Hz, q={bandgap_q})"

    plt.gcf().text(
        0.01, 0.01,               # position: bottom-right corner
        name,                    # the stamped text
        ha='left', va='bottom', # anchor
        fontsize=12,
        alpha=0.8                # slightly transparent
    )

    if export_dir:
        Path(export_dir).mkdir(parents=True, exist_ok=True)
        outfile = Path(export_dir) / (Path(src).stem + ".png")
        plt.savefig(str(outfile))

    else:
        plt.show()
   


# ---------- MAIN ----------

def main(file_path):

    df, marker_indices, column_names, sample_rate = load_file(file_path)
    if(sample_rate == 0): 
        return
    
    df = apply_filtering(df, filter_window, sample_rate, bandgap_freq, bandgap_q)

    # Compute pre-normalization stddev
    pre_std = df.iloc[marker_indices[1]:marker_indices[-2]].std().values

    segments = extract_segments(df, marker_indices)
    stacked, target_len = normalize_segments(segments)
    plot_segments(stacked, target_len, column_names, file_path, pre_std)



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py data.xml")
        sys.exit(1)
    main(sys.argv[1])
