#!/usr/bin/python
import sys
import os
import numpy as np
import numpy as np
from scipy.interpolate import interp1d
from scipy.stats import pearsonr
import matplotlib.pyplot as plt
from pathlib import Path
from load import load_file
from filtering import apply_filtering, extract_segments
src = sys.argv[1]  # existing positional argument
export_dir = os.getenv("EXPORT_DIR")
filter_window = float(os.getenv("FILTER_WINDOW", "0"))  # default: no filter
bandgap_freq = float(os.getenv("BANDGAP_FREQ", "0"))  # default: no filter
bandgap_q = float(os.getenv("BANDGAP_Q", "0"))  # default: no filter

def normalize_segments(segments):
    """Resample segments to shortest length, then z-score normalize each."""
    target_len = 25*20
    normalized = []

    for seg in segments:
        x_old = np.linspace(0, 1, len(seg))
        x_new = np.linspace(0, 1, target_len)
        interp = interp1d(x_old, seg.values, axis=0, kind='linear')
        resampled = interp(x_new)
        resampled = (resampled - resampled.mean(axis=0)) 
        normalized.append(resampled)

    return np.stack(normalized)

# ---------- STATISTICS & CORRELATION (NEW) ----------

def analyze_correlations(stacks, set_names, column_names):
    """
    Calculates Pearson correlation between the mean trajectories of different files.
    1. Prints a table of per-sensor correlations if comparing 2 files.
    2. Plots a heatmap matrix of average correlations between all files.
    """
    num_sets = len(stacks)
    if num_sets < 2:
        print("Need at least 2 datasets to calculate correlation.")
        return

    # Calculate mean signal (Time x Sensors) for each subject/file
    # means[i] is the average response for file i
    means = [s.mean(axis=0) for s in stacks] 
    num_sensors = means[0].shape[1]

    # --- 1. Console Output (Detailed) ---
    # print("\n" + "="*40)
    # print("       PEARSON CORRELATION ANALYSIS       ")
    # print("="*40)
    
    # If exactly 2 files, give granular per-sensor detail
    if num_sets == 2:
        print(f"\nComparing: '{set_names[0]}' vs '{set_names[1]}'")
        print(f"{'Sensor':<15} | {'Correlation (r)':<15}")
        print("-" * 35)
        
        corrs = []
        for ch in range(num_sensors):
            # Calculate r for this specific sensor between file 0 and file 1
            r, pvalue = pearsonr(means[0][:, ch], means[1][:, ch])
            corrs.append(r)
            # print(f"{column_names[ch][:12]:<15} | {r:.4f}")
        
        print("-" * 35)
        print(f"{'AVERAGE':<15} | {np.mean(corrs):.4f}")

    # --- 2. Matrix Calculation (Global Similarity) ---
    # We calculate a matrix where Cell [i,j] is the average correlation 
    # across all sensors between File i and File j.
    corr_matrix = np.zeros((num_sets, num_sets))

    for i in range(num_sets):
        for j in range(num_sets):
            if i == j:
                corr_matrix[i, j] = 1.0
            else:
                # Calculate r for every sensor, then average them
                sensor_corrs = []
                for ch in range(num_sensors):
                    r, pvalue = pearsonr(means[i][:, ch], means[j][:, ch])
                    if(pvalue < 0.05):
                        sensor_corrs.append(r)
                        # print(f"channel {ch}, pvalue {pvalue}")
                    else:
                        sensor_corrs.append(0)
                corr_matrix[i, j] = np.mean(sensor_corrs)

    # --- 3. Plot Heatmap ---
    fig, ax = plt.subplots(figsize=(6 + num_sets, 5 + num_sets * 0.5))
    im = ax.imshow(corr_matrix, cmap='RdYlGn', vmin=-1, vmax=1)
    
    # Add colorbar
    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel("Pearson Correlation (r)", rotation=-90, va="bottom")

    # Show all ticks and label them
    ax.set_xticks(np.arange(num_sets))
    ax.set_yticks(np.arange(num_sets))
    ax.set_xticklabels(set_names)
    ax.set_yticklabels(set_names)

    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    # Loop over data dimensions and create text annotations.
    for i in range(num_sets):
        for j in range(num_sets):
            text = ax.text(j, i, f"{corr_matrix[i, j]:.2f}",
                           ha="center", va="center", color="black", fontweight="bold")

    ax.set_title("Average Signal Correlation Between Subjects")
    fig.tight_layout()
    plt.subplots_adjust(bottom=0.2)


# ---------- PLOTTING ----------

def plot_segments(stacks, column_names, set_names=None):
    import matplotlib.widgets as mwidgets
    import itertools

    num_sets = len(stacks)
    if set_names is None:
        set_names = [f"Set {i+1}" for i in range(num_sets)]

    num_sensors = stacks[0].shape[2]
    example_mean = stacks[0].mean(axis=0)
    T = example_mean.shape[0]
    time = np.linspace(0, 1, T)

    rows, cols = 4, 4
    fig, axes = plt.subplots(rows, cols, figsize=(12, 3 * rows), sharex=True)
    axes = axes.flatten()

    base_colors = plt.cm.tab10.colors
    set_colors = list(itertools.islice(itertools.cycle(base_colors), num_sets))

    lines_per_set = [[] for _ in range(num_sets)]

    for ch in range(num_sensors):
        ax = axes[ch]
        for set_idx, stacked in enumerate(stacks):
            mean_seg = stacked.mean(axis=0)
            curve = mean_seg[:, ch]
            line, = ax.plot(
                time,
                curve,
                color=set_colors[set_idx],
                label=set_names[set_idx] if ch == 0 else None
            )
            lines_per_set[set_idx].append(line)

        ax.set_title(column_names[ch][:12])
        ax.set_ylabel("Norm. Change")
        ax.grid(True)

    for ax in axes[num_sensors:]:
        fig.delaxes(ax)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', ncol=num_sets)

    plt.xlabel("Normalized Time (0 → 1)")
    plt.tight_layout(rect=[0, 0.05, 1, 0.92])

    # --- Toggle buttons ---
    button_height = 0.025
    button_width = 0.1
    spacing = 0.012
    start_x = 0.02
    start_y = 0.01

    def make_toggle_callback(lines):
        def callback(event):
            visible = not lines[0].get_visible()
            for l in lines:
                l.set_visible(visible)
            plt.draw()
        return callback

    buttons = [] 
    for i, set_name in enumerate(set_names):
        ax_button = fig.add_axes([start_x + i*(button_width+spacing), start_y, button_width, button_height])
        button = mwidgets.Button(ax_button, f"{set_name}")
        button.on_clicked(make_toggle_callback(lines_per_set[i]))
        buttons.append(button)

    fig._buttons = buttons 

    # Handle export
    if len(sys.argv) > 1:
        src = sys.argv[1]
        name = Path(src).stem
    else:
        name = "output"
    
    export_dir = locals().get('export_dir', None) # Safety for local scope vs global

    if export_dir:
        Path(export_dir).mkdir(parents=True, exist_ok=True)
        outfile = Path(export_dir) / (name + ".png")
        plt.savefig(str(outfile))
    
    # We do NOT call plt.show() here yet, because we want the correlation plot to show up too


# ---------- MAIN ----------

def main(file_paths):
    stacks = []
    set_names = []
    column_names = ""

    # 1. Process all files
    for f in file_paths[1:]:
        df, marker_indices, column_names, sample_rate = load_file(f)
        if(sample_rate == 0):
            continue
        df = apply_filtering(df, filter_window, sample_rate, bandgap_freq, bandgap_q)

        segments = extract_segments(df, marker_indices)
        stacked = normalize_segments(segments)

        stacks.append(stacked)
        set_names.append(Path(f).stem)  

    # 2. Analyze Correlations (New Step)
    if len(stacks) > 1:
        analyze_correlations(stacks, set_names, column_names)

    # 3. Plot Main Data
    plot_segments(stacks, column_names, set_names=set_names)

    # Final show for all figures generated
    plt.show()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py data1.xml data2.xml ...")
        sys.exit(1)
    main(sys.argv)
