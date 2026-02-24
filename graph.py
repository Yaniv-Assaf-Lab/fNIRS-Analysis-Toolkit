#!/usr/bin/python
import os
import sys
import argparse
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ---------- UNIFIED PLOTTING ----------

def plot_data(stacked, column_names, name, mode, skill, output_dir):
    """
    Unified plotter with descriptive titles for the figure and subplots.
    """
    target_len = stacked.shape[1]
    num_sensors = stacked.shape[2]
    time = np.linspace(0, 1, target_len)
    
    # Grid setup: 8 subplots (4 rows, 2 columns)
    fig, axes = plt.subplots(4, 2, figsize=(12, 13), sharex=True)
    axes = axes.flatten()
    
    # --- Meaningful Figure Title ---
    # Capitalize mode for better presentation
    display_mode = str(mode).capitalize()
    main_title = f"fNIRS Analysis: {name}\nSkill Level: {skill}m | Mode: {display_mode}"
    fig.suptitle(main_title, fontsize=14, y=0.98)
    
    fig.canvas.manager.set_window_title(f"{name} - {display_mode}")

    # Determine mode type
    is_diff_mode = (mode != None)

    for i in range(8):
        ax = axes[i]
        
        if is_diff_mode:
            # --- Subtract Mode (8 Channels) ---
            if i < num_sensors:
                mean_vals = stacked.mean(axis=0)[:, i]
                std_vals = stacked.std(axis=0)[:, i]
                
                ax.plot(time, mean_vals, label="$\Delta$ Hb (Diff)", color="teal", linewidth=1.5)
                ax.fill_between(time, mean_vals - std_vals, mean_vals + std_vals, alpha=0.3, color="teal")
                
                # Title based on the pair used for subtraction
                title_text = column_names[i*2] if (i*2) < len(column_names) else f"Channel {i}"
                ax.set_title(f"Channel {i+1}: {title_text[:15]}", fontsize=10)
        else:
            # --- Dual Mode (16 Sensors: O2Hb & HHb) ---
            colors = ["#d62728", "#1f77b4"] # Strong Red and Blue
            labels = ["O2Hb", "HHb"]
            
            for j in range(2):
                sensor_idx = i * 2 + j
                if sensor_idx < num_sensors:
                    mean_vals = stacked.mean(axis=0)[:, sensor_idx]
                    std_vals = stacked.std(axis=0)[:, sensor_idx]
                    
                    ax.plot(time, mean_vals, label=labels[j], color=colors[j], linewidth=1.2)
                    ax.fill_between(time, mean_vals - std_vals, mean_vals + std_vals, alpha=0.2, color=colors[j])
            
            title_idx = i * 2
            if title_idx < len(column_names):
                ax.set_title(f"Channel {i+1}: {column_names[title_idx][:15]}", fontsize=10)

        ax.set_ylabel("Norm. $\Delta$ Intensity")
        ax.grid(True, linestyle='--', alpha=0.4)
        ax.legend(fontsize="small", loc="upper right")

    plt.xlabel("Normalized Trial Duration (0% → 100%)", fontsize=11)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # Adjust layout to make room for suptitle

    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        suffix = "_diff" if is_diff_mode else ""
        outfile = Path(output_dir) / f"{name}{suffix}.png"
        plt.savefig(str(outfile), dpi=200) # Higher DPI for "meaningful" reports
        print(f"Plot saved to: {outfile}")
    else:
        plt.show()

# ---------- MAIN ----------

def main():
    parser = argparse.ArgumentParser(description="Visualize a specific analyzed .npz file.")
    parser.add_argument("file_path", help="Path to the .npz data file")
    parser.add_argument("-o", "--output_dir", help="Directory to save the plot")
    args = parser.parse_args()

    file_path = Path(args.file_path)
    if not file_path.exists():
        print(f"Error: File '{args.file_path}' not found.")
        sys.exit(1)

    with np.load(file_path, allow_pickle=True) as data:
        try:

            mode = data['mode']
            name = data['name']
            skill = data['skill']
            
            plot_data(
                stacked=data['stack'],
                column_names=data['column_names'],
                name=name,
                mode=mode,
                skill=skill,
                output_dir=args.output_dir
            )
        except KeyError as e:
            print(f"Error: Missing key {e} in {file_path.name}")
            sys.exit(1)

if __name__ == "__main__":
    main()