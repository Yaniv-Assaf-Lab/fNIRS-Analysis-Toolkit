#!/usr/bin/python
import sys
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from load import load_file
from filtering import apply_filtering, extract_segments, retime_segments

# Plotting

def plot_trial(trial, column_names, subject_id, pre_std, output_dir=None):
    stacked = np.array(trial)
    target_len = stacked.shape[1]
    num_sensors = stacked.shape[2]
    time = np.linspace(0, 20, target_len)

    fig, axes = plt.subplots(4, 2, figsize=(12, 13), sharex=True)
    axes = axes.flatten()

    title_id = f"{subject_id}"
    main_title = f"fNIRS Analysis: {title_id}"
    fig.suptitle(main_title, fontsize=14, y=0.98)

    fig.canvas.manager.set_window_title(title_id)

    for i in range(8):
        ax = axes[i]

        if i < num_sensors:
            mean_vals = stacked.mean(axis=0)[:, i]
            std_vals = stacked.std(axis=0)[:, i]

            ax.plot(time, mean_vals, linewidth=1.5)
            ax.fill_between(time, mean_vals - std_vals, mean_vals + std_vals, alpha=0.3)

            title_text = rf"$\Delta$ {column_names[2*i][:5]}, $\sigma = {pre_std[i]:.2f}$"
            ax.set_title(f"Channel {i+1}: {title_text}", fontsize=10)

        ax.set_ylabel(r"Norm. $\Delta$Hb")
        ax.grid(True, linestyle='--', alpha=0.4)
        ax.legend(fontsize="small", loc="upper right")

    plt.xlabel("Trial Duration [sec]", fontsize=11)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        outfile = Path(output_dir) / str(title_id)
        plt.savefig(str(outfile), dpi=200)
        print(f"Plot saved to: {outfile}")
        plt.close(fig)
    else:
        plt.show()

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

def main(file_path):
    filter_window = 1
    bandgap_freq = 1.5 
    bandgap_q = 3
    subject_id = Path(file_path).stem

    df, marker_indices, column_names, sample_rate = load_file(file_path)
    if(sample_rate == 0): 
        return
    
    df = apply_filtering(df, filter_window, sample_rate, bandgap_freq, bandgap_q)
    
    # Compute pre-normalization stddev
    df = subtract_channels(df)
    pre_std = df.iloc[marker_indices[1]:marker_indices[-3]].std().values
    segments = extract_segments(df, marker_indices)
    stacked = retime_segments(segments)
    stacked = stacked[:-1] - stacked[-1]
    plot_trial(stacked, column_names, subject_id, pre_std, output_dir=None)



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:\n./analyze-one.py data{.xml/.snirf}\nOR\npython analyze-one.py data{.xml/.snirf}")
        sys.exit(1)
    main(sys.argv[1])