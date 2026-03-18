#!/usr/bin/python
import sys
import argparse
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from filenames import generate_title, generate_image_filename
# ---------- UNIFIED PLOTTING ----------

def plot_data(stacked, column_names, id, analysis, subject, output_dir):
    """
    Unified plotter with descriptive titles for the figure and subplots.
    """
    skill = subject["skill"]
    target_len = stacked.shape[1]
    num_sensors = stacked.shape[2]
    time = np.linspace(0, 1, target_len)
    
    fig, axes = plt.subplots(4, 2, figsize=(12, 13), sharex=True)
    axes = axes.flatten()

    main_title = f"fNIRS Analysis: {id}\nSkill Level: {skill}m | {generate_title(analysis)}"
    fig.suptitle(main_title, fontsize=14, y=0.98)
    
    fig.canvas.manager.set_window_title(f"{id}")

    for i in range(8):
        ax = axes[i]
        if analysis['transform'] != None:
            # --- Subtract Mode (8 Channels) ---
            if i < num_sensors:
                mean_vals = stacked.mean(axis=0)[:, i]
                std_vals = stacked.std(axis=0)[:, i]
                
                ax.plot(time, mean_vals, label=r"$\Delta$ Hb (Diff)", color="teal", linewidth=1.5)
                ax.fill_between(time, mean_vals - std_vals, mean_vals + std_vals, alpha=0.3, color="teal")
                
                # Title based on the pair used for subtraction
                title_text = column_names[i]
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

        ax.set_ylabel(r"Norm. $\Delta$ Intensity")
        ax.grid(True, linestyle='--', alpha=0.4)
        ax.legend(fontsize="small", loc="upper right")

    plt.xlabel("Normalized Trial Duration (0% → 100%)", fontsize=11)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # Adjust layout to make room for suptitle

    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        outfile = Path(output_dir) / generate_image_filename(id, analysis)
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

            analysis = data['analysis'].item()
            id = data['id']
            subject = data['subject'].item()
            
            plot_data(
                stacked=data['stack'],
                column_names=data['column_names'],
                id=id,
                analysis=analysis,
                subject=subject,
                output_dir=args.output_dir,
            )
        except KeyError as e:
            print(f"Error: Missing key {e} in {file_path.name}")
            sys.exit(1)

if __name__ == "__main__":
    main()