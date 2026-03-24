#!/usr/bin/python
import sys
import os
import numpy as np
from scipy.stats import pearsonr
import matplotlib.pyplot as plt
from pathlib import Path
import argparse
from filenames import generate_title, generate_image_filename
from collections import defaultdict 

p_value_threshold = 0.05

belt_order = [
    "unkn",
    "whte",
    "blue",
    "prpl",
    "brwn",
    "blck"
]

def group_by_field(processed_data, field):
    grouped = defaultdict(list)

    for item in processed_data:
        key = item['subject'][field]
        grouped[key].append(item['stack'])  # <-- append, not extend

    result = []
    for key, stack_list in grouped.items():
        combined_stack = np.concatenate(stack_list, axis=0)

        result.append({
            'stack': combined_stack,
            'id': key,
            'subject': None,
            'trial': 0
        })

    return result

def plot_correlations(stacks, set_names, analysis, args):
    """
    Calculates Pearson correlation between mean trajectories.
    Works for both 16-channel and 8-channel.
    """
    num_sets = len(stacks)
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

    ax.set_title(f"Signal Correlation Between Subjects\n{generate_title(analysis)}")

    fig.tight_layout()
    if(args["save"]):
        Path(args["save"]).mkdir(parents=True, exist_ok=True)
        outfile = Path(args["save"]) / generate_image_filename("correlations", analysis)
        plt.savefig(str(outfile), dpi=200) # Higher DPI for "meaningful" reports
        print(f"Plot saved to: {outfile}")
    else:
       plt.show() 

def plot_correlations_per_sensor(stacks, set_names, analysis, column_names, output_dir):
    """
    Calculates Pearson correlation between mean trajectories
    and opens one NON-BLOCKING window per sensor.
    """
    plt.ion()  # Turn on interactive mode

    num_sets = len(stacks)
    means = [s.mean(axis=0) for s in stacks]
    num_sensors = means[0].shape[1]

    p_thresh = 0.05

    # Compute correlation matrices per sensor
    corr_matrices = np.zeros((num_sensors, num_sets, num_sets))

    for ch in range(num_sensors):
        for i in range(num_sets):
            for j in range(num_sets):
                if i == j:
                    corr_matrices[ch, i, j] = 100.0
                else:
                    r, pvalue = pearsonr(means[i][:, ch], means[j][:, ch])
                    corr_matrices[ch, i, j] = (100 * r) if pvalue < p_thresh else 0

    # ---- Open separate NON-BLOCKING window per sensor ----
    for ch in range(num_sensors):
        plt.rcParams["figure.dpi"] = 67
        px = 1/plt.rcParams['figure.dpi']  # pixel in inches
        fig, ax = plt.subplots(figsize=(1024*px, 720*px)) #(width, height)
        fig.canvas.manager.set_window_title(f"Sensor {ch+1}: {column_names[ch]}")

        im = ax.imshow(corr_matrices[ch], cmap='RdYlGn', vmin=-100, vmax=100)

        cbar = fig.colorbar(im, ax=ax)
        cbar.set_label("Pearson Correlation (r) × 100")

        ax.set_xticks(np.arange(num_sets))
        ax.set_yticks(np.arange(num_sets))
        ax.set_xticklabels(set_names, rotation=45, ha="right")
        ax.set_yticklabels(set_names)

        for i in range(num_sets):
            for j in range(num_sets):
                ax.text(j, i, f"{corr_matrices[ch, i, j]:.0f}",
                        ha="center", va="center",
                        color="black", fontweight="bold")


        ax.set_title(f"Signal Correlation Between Subjects\n"
                     f"Channel {ch+1} | {generate_title(analysis)}")

        fig.tight_layout()

        if(output_dir):
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            outfile = Path(output_dir) / generate_image_filename("correlations", analysis, id = column_names[ch])
            plt.savefig(str(outfile), dpi=200) # Higher DPI for "meaningful" reports
            print(f"Plot saved to: {outfile}")
        else:
            plt.show(block=False)  # <- Non-blocking
            plt.pause(0.1)         # <- Ensures window renders properly

    plt.show(block=True)
    

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
    analysis = None
    # 1. Process all files
    for f in file_paths:
        data = np.load(f, allow_pickle=True)
        stack = data["stack"]
        column_names = data["column_names"]
        trial = data["trial"]
        analysis = data['analysis'].item()
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
        processed_data.sort(
            key=lambda x: belt_order.index(x["subject"][args["sort"]]) if x["subject"][args["sort"]] in belt_order else x["subject"][args["sort"]]
        ,reverse = True)

    if(args["filter"]):
        field, value = args["filter"]
        processed_data = [
            item for item in processed_data
            if item["subject"].get(field) == value
        ]

    if (args['group']):
        processed_data = group_by_field(processed_data, args['group'])
        processed_data.sort(
            key=lambda x: belt_order.index(x['id']) if x['id'] in belt_order else x['id']
        ,reverse = True)

    # 3. Unpack into separate lists for the correlation function
    stacks = []
    set_names = []
    for item in processed_data:
        stacks.append(item['stack'])
        subj = item['subject']
        if(args['sort'] and not args['group']):
            set_names.append(f"{item['id']}_{item['trial']} ({subj[args['sort']]})")
        else:
            if(item['trial'] == 0):
                set_names.append(f"{item['id']}")
            else:
                set_names.append(f"{item['id']}_{item['trial']}")

    # Analyze Correlations
    if args["split"]:
        plot_correlations_per_sensor(stacks, set_names, analysis, column_names, args['save'])
    else:
        plot_correlations(stacks, set_names, analysis, args)


if __name__ == "__main__":

    fields = ["age", "skill", "belt", "gender", "handedness"] # Change this to change fields
    parser = argparse.ArgumentParser(
                    description='View correlations between all subjects in a directory')

    parser.add_argument('input_dir')
    parser.add_argument('-s', '--sort', metavar = 'sort', choices = fields, help = 
                        "Allows sorting by a specified parameter"
                        )
    parser.add_argument('-f', '--filter', metavar=("field", "value"), nargs = 2, help = 
                        "Allows filtering by a specified field and value"
                        )
    parser.add_argument('-p', '--split', action=argparse.BooleanOptionalAction, default = False, help = 
                        "Normally the correlation is averaged between all channels, in order to create one correlation matrix. Enabling this option allows for the creation of separate correlation matrices, one for each sensor channel."
                        )
    parser.add_argument('-g', '--group', metavar='group', choices = fields, help = 
                        "Group participants by parameter, and show average correlations between groups. Incompatible with --split."
                        )
    parser.add_argument('-a', '--save', metavar='save_dir', help = 
                        "Allows saving of the resulting matrix to an image."
                        )
    
    args = vars(parser.parse_args(sys.argv[1:]))
    main(args)
