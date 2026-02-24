#!/usr/bin/python
import sys
import os
import numpy as np
from scipy.stats import pearsonr
import matplotlib.pyplot as plt
import matplotlib.widgets as mwidgets
import itertools
from pathlib import Path
import argparse

p_value_threshold = 0.05

def plot_correlations(stacks, set_names, analysis_mode):
    """
    Calculates Pearson correlation between mean trajectories.
    Works for both 16-channel and 8-channel.
    """
    num_sets = len(stacks)
    differential = True if (analysis_mode != None) else False 
    # means[i] shape: (Time, Sensors)
    means = [s.mean(axis=0) for s in stacks] 
    num_sensors = means[0].shape[1]
    
    # Define p-value threshold (adjust if this is a global variable in your script)
    p_thresh = 0.05

    # --- Matrix Calculation ---
    corr_matrix = np.zeros((num_sets, num_sets))
    for i in range(num_sets):
        for j in range(num_sets):
            if i == j:
                corr_matrix[i, j] = 100.0
            else:
                sensor_corrs = []
                for ch in range(num_sensors):
                    r, pvalue = pearsonr(means[i][:, ch], means[j][:, ch])
                    # Only include significant correlations, else treat as 0
                    sensor_corrs.append((100 * r) if pvalue < p_thresh else 0)
                corr_matrix[i, j] = np.mean(sensor_corrs)

    
    # --- Plot Heatmap ---
    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(corr_matrix, cmap='RdYlGn', vmin=-100, vmax=100)
    
    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel("Avg Pearson Correlation (r)", rotation=-90, va="bottom")

    ax.set_xticks(np.arange(num_sets))
    ax.set_yticks(np.arange(num_sets))
    ax.set_xticklabels(set_names, rotation=45, ha="right")
    ax.set_yticklabels(set_names)

    for i in range(num_sets):
        for j in range(num_sets):
            ax.text(j, i, f"{corr_matrix[i, j]:.0f}",
                    ha="center", va="center", color="black", fontweight="bold")

    title_suffix = f"(Differential 8-Ch, mode = {analysis_mode})" if differential else "(Raw 16-Ch)"
    ax.set_title(f"Signal Correlation Between Subjects\n{title_suffix}")
    fig.tight_layout()


# ---------- PLOTTING ----------

def plot_segments(stacks, column_names, analysis_mode, set_names=None):
   
    num_sets = len(stacks)
    if set_names is None:
        set_names = [f"Set {i+1}" for i in range(num_sets)]

    # Detect if we have 8 (subtracted) or 16 (raw) channels
    num_sensors = stacks[0].shape[2]
    example_mean = stacks[0].mean(axis=0)
    T = example_mean.shape[0]
    time = np.linspace(0, 1, T)

    # --- Dynamic Grid Logic ---
    if analysis_mode != None:
        rows, cols = 4, 2
    else:
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
            
            # Plot mean trajectory
            line, = ax.plot(
                time,
                curve,
                color=set_colors[set_idx],
                label=set_names[set_idx] if ch == 0 else None,
                alpha=0.8
            )
            lines_per_set[set_idx].append(line)

        # Use the provided column names (8 names if subtracted, 16 if not)
        title = column_names[ch] if ch < len(column_names) else f"Ch {ch}"
        ax.set_title(title[:20], fontsize=10)
        ax.set_ylabel("Norm. Δ")
        ax.grid(True, linestyle='--', alpha=0.6)

    # Hide unused subplots if num_sensors is not a multiple of grid size
    for ax in axes[num_sensors:]:
        fig.delaxes(ax)

    # Adjust legend and layout
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', ncol=min(num_sets, 4), fontsize='small')

    plt.xlabel("Normalized Time (0 → 1)")
    plt.tight_layout(rect=[0, 0.05, 1, 0.94])

    # --- Interactive Toggle Buttons ---
    button_height = 0.03
    button_width = 1 / (1.3 * num_sets)
    spacing = 0.01
    start_x = 0.05
    start_y = 0.01

    def make_toggle_callback(lines):
        def callback(event):
            visible = not lines[0].get_visible()
            for l in lines:
                l.set_visible(visible)
                # If you added fill_betweens later, toggle them here too
            plt.draw()
        return callback

    buttons = [] 
    for i, set_name in enumerate(set_names):
        # Prevent buttons from overlapping or going off-screen
        ax_button = fig.add_axes([start_x + i*(button_width+spacing), start_y, button_width, button_height])
        button = mwidgets.Button(ax_button, f"{set_name}", color='lightgray', hovercolor='0.975')
        button.on_clicked(make_toggle_callback(lines_per_set[i]))
        buttons.append(button)

    fig._buttons = buttons 
    
    # Export logic
    if len(sys.argv) > 1:
        src = sys.argv[1]
        name = f"{Path(src).stem}_comparison"
    else:
        name = "multi_subject_plot"
    
    # Note: Ensure export_dir is accessible (passed as arg or global)
    if 'export_dir' in globals() and globals()['export_dir']:
        path = Path(globals()['export_dir'])
        path.mkdir(parents=True, exist_ok=True)
        plt.savefig(path / f"{name}.png")

# ---------- MAIN ----------



def main(args):
    file_paths = []
    with os.scandir(args["input_dir"]) as dir:
        for entry in dir:
            if entry.is_file():
                file_paths.append(os.path.join(args["input_dir"], entry.name))
                
    # Use a list to store objects containing (skill, stack, name)
    processed_data = []
    column_names = ""
    analysis_mode = None
    # 1. Process all files
    for f in file_paths:
        data = np.load(f, allow_pickle=True)
        stack = data["stack"]
        column_names = data["column_names"]
        trial = data["trial"]
        analysis_mode = data["mode"]
        subject = data["subject"].item()
        id = data["id"]

        if(subject == 0):
            print(f"Subject not found: {f}")
            exit(1)
        
        # 3. Store as a tuple to keep them linked
        processed_data.append({
            'stack': stack,
            'id': id,
            'subject': subject,
            'trial': trial
        })

    # 2. Sort the entire list by the 'skill' key
    # Change reverse=True if you want most experienced first
    if(args["sort"]):
        processed_data.sort(key=lambda x: x["subject"][args["sort"]], reverse = True)

    if(args["filter"]):
        field, value = args["filter"]
        processed_data = [
            item for item in processed_data
            if item["subject"].get(field) == value
        ]

    # 3. Unpack into separate lists for the correlation function
    stacks = []
    set_names = []
    for item in processed_data:
        stacks.append(item['stack'])
        subj = item['subject']
        if(args["sort"]):
            set_names.append(f"{item['id']}_{item['trial']} ({subj[args["sort"]]})")
        else:
            set_names.append(f"{item['id']}_{item['trial']}")

    # Analyze Correlations
    if args["mode"] == "correlate":
        plot_correlations(stacks, set_names, analysis_mode)
    if args["mode"] == "plot":
        # If you also want to plot the segments
        # (Kinda broken for many participants)
        plot_segments(stacks, column_names, analysis_mode, set_names)
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog='fNIRS-analyze',
                    description='Analyzer for fNIRS data')

    parser.add_argument('input_dir')
    parser.add_argument('-m', '--mode', metavar = 'mode', required = True, choices=['plot', 'correlate'])
    parser.add_argument('-s', '--sort', metavar = 'sort', choices=["age", "skill", "belt", "gender", "handedness"])
    parser.add_argument('-f', '--filter', metavar=("field", "value"), nargs = 2)
    args = vars(parser.parse_args(sys.argv[1:]))
    main(args)
