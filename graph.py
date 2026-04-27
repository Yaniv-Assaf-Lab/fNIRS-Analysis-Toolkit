#!/usr/bin/python
import sys
import argparse
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from filenames import generate_title, generate_image_filename

# ---------- PLOTTING ----------

def plot_trial(trial, column_names, analysis, output_dir):
    stacked = np.array(trial['stacks'])

    if args["offset"] and analysis.get("phase_locked", False):
        offset = int(trial.get("offset", 0))
        if offset > 0:
            stacked = stacked[:, offset:, :]
        elif offset < 0:
            stacked = stacked[:, :offset, :]

    subject = trial['subject']
    subject_id = trial['subject_id']
    trial_idx = trial['index']

    skill = subject["skill"] if subject else "unknown"

    target_len = stacked.shape[1]
    num_sensors = stacked.shape[2]
    time = np.linspace(0, 1, target_len)

    fig, axes = plt.subplots(4, 2, figsize=(12, 13), sharex=True)
    axes = axes.flatten()

    title_id = f"{subject_id}" if trial_idx == 1 else f"{subject_id} [{trial_idx}]"
    main_title = f"fNIRS Analysis: {title_id}\nSkill Level: {skill} | {generate_title(analysis, num_sensors)}"
    fig.suptitle(main_title, fontsize=14, y=0.98)

    fig.canvas.manager.set_window_title(title_id)

    for i in range(8):
        ax = axes[i]

        if analysis['transform'] is not None:
            # --- 8-channel (transformed) ---
            if i < num_sensors:
                mean_vals = stacked.mean(axis=0)[:, i]
                std_vals = stacked.std(axis=0)[:, i]

                ax.plot(time, mean_vals, linewidth=1.5)
                ax.fill_between(time, mean_vals - std_vals, mean_vals + std_vals, alpha=0.3)

                title_text = column_names[i]
                ax.set_title(f"Channel {i+1}: {title_text[:15]}", fontsize=10)

        else:
            # --- 16-channel (O2Hb + HHb) ---
            colors = ["red", "blue"]
            labels = ["O2Hb", "HHb"]

            for j in range(2):
                sensor_idx = i * 2 + j
                if sensor_idx < num_sensors:
                    mean_vals = stacked.mean(axis=0)[:, sensor_idx]
                    std_vals = stacked.std(axis=0)[:, sensor_idx]

                    ax.plot(time, mean_vals, label=labels[j], color=colors[j], linewidth=1.2)
                    ax.fill_between(time, mean_vals - std_vals, mean_vals + std_vals,
                                    alpha=0.2, color=colors[j])

            title_idx = i * 2
            if title_idx < len(column_names):
                ax.set_title(f"Channel {i+1}: {column_names[title_idx][:15]}", fontsize=10)

        ax.set_ylabel(r"Norm. $\Delta$ Intensity")
        ax.grid(True, linestyle='--', alpha=0.4)
        ax.legend(fontsize="small", loc="upper right")

    plt.xlabel("Normalized Trial Duration (0% → 100%)", fontsize=11)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        outfile = Path(output_dir) / generate_image_filename(title_id, analysis)
        plt.savefig(str(outfile), dpi=200)
        print(f"Plot saved to: {outfile}")
        plt.close(fig)
    else:
        plt.show()


# ---------- MAIN ----------

def main(args):
    if not Path(args["input_file"]).exists():
        print(f"Error: File '{args['input_file']}' not found.")
        sys.exit(1)

    fNIRS_Data = np.load(args["input_file"], allow_pickle=True)['fNIRS_Data'].item()

    trials = fNIRS_Data['trials']
    column_names = fNIRS_Data['column_names']
    analysis = fNIRS_Data['analysis']

    # --- Optional filtering (like correlate.py) ---
    if args["filter"]:
        field, value = args["filter"]
        trials = [
            t for t in trials
            if t["subject"] and t["subject"].get(field) == value
        ]

    if args["subject"]:
        trials = [
            t for t in trials
            if t["subject_id"] == args["subject"]
        ]

    if not trials:
        print("No trials matched the selection.")
        return

    # --- Plot all selected trials ---
    for trial in trials:
        plot_trial(trial, column_names, analysis, args["output_dir"])


if __name__ == "__main__":
    fields = ["age", "skill", "belt", "gender", "handedness"]

    parser = argparse.ArgumentParser(
        description="Visualize trials from analyzed fNIRS dataset"
    )

    parser.add_argument("input_file", help="Path to analyzed .npz file")
    parser.add_argument("-d", "--output_dir", help="Directory to save plots")

    parser.add_argument("-f", "--filter", metavar=("field", "value"), nargs=2,
                        help="Filter by subject field")

    parser.add_argument("-s", "--subject", help="Plot only a specific subject_id")
    parser.add_argument('--offset', action=argparse.BooleanOptionalAction, default = True, help = 
                        "Parameter to take offset into account, as long as the analyzed data includes it."
                        )

    args = vars(parser.parse_args(sys.argv[1:]))

    main(args)