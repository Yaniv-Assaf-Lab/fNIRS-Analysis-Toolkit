#!/usr/bin/python
import sys
import os
import numpy as np
from scipy.stats import pearsonr
from scipy.signal import correlate, correlation_lags
import matplotlib.pyplot as plt
from pathlib import Path
import argparse
from filenames import generate_title, generate_image_filename
from collections import defaultdict 

belt_order = [
    "unkn",
    "whte",
    "blue",
    "prpl",
    "brwn",
    "blck"
]

# cross_correlation = correlate(means[i][:, ch], means[j][:, ch])
# arraylength = len(means[i][:, ch])
# max_correlation = np.argmax(cross_correlation[int(arraylength // 2) : int(arraylength * 1.5)])
# sensor_corrs.append(max_correlation)


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
            'subject_id': key,
            'subject': None,
            'trial': 0
        })

    return result

def plot_correlations(trials, set_names, analysis, args):
    """
    Calculates Pearson correlation between mean trajectories.
    Works for both 16-channel and 8-channel.
    """
    num_sets = len(trials)
    # means shape: (Trials, Time, Sensors)
    # means = np.array([trial['stacks'].mean(axis=0) for trial in trials])[::,::,::2] # HbO Only
    means = np.array([trial['stacks'].mean(axis=0) for trial in trials])
    offsets = np.array([trial['offset'] for trial in trials])
    
    num_sensors = means[0].shape[1]


    # Align trials according to offset
    min_len = means.shape[1] - int(np.max(offsets) - np.min(offsets))
    aligned = []
    if(args['offset']):
        for i, mean in enumerate(means):
            shifted = np.roll(mean, offsets[i])
            aligned.append(shifted[:min_len])

        means = np.array(aligned)

    print(f"means shape: {means.shape}")
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
                    sensor_corrs.append((100 * r) if pvalue < 0.05 else 0)
                    
                corr_matrix[i, j] = np.mean(sensor_corrs)
                # corr_matrix[i, j] = np.median(sensor_corrs)

    
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

    ax.set_title(f"Signal Correlation Between Subjects\n{generate_title(analysis, means.shape[2])}")

    fig.tight_layout()
    if(args["save"]):
        Path(args["save"]).mkdir(parents=True, exist_ok=True)
        outfile = Path(args["save"]) / generate_image_filename("correlations", analysis)
        plt.savefig(str(outfile), dpi=200) # Higher DPI for "meaningful" reports
        print(f"Plot saved to: {outfile}")
    else:
       plt.show() 


# ---------- MAIN ----------

def main(args):                


    # Load fNIRS Data
    fNIRS_Data = None
    if(os.path.isfile(args["input_file"])):
        fNIRS_Data = np.load(args["input_file"], allow_pickle=True)['fNIRS_Data'].item()

    # Process all trials into an array for filtering
    trials_array = []
    for trial in fNIRS_Data['trials']:
        subject_id = trial["subject_id"]
        if(subject_id == -1): # For skipping testing data
            continue

        trials_array.append(trial)

    # Sort and filter
    if(args["sort"]):
        trials_array.sort(
            key=lambda x: belt_order.index(x["subject"][args["sort"]]) if x["subject"][args["sort"]] in belt_order else x["subject"][args["sort"]]
        ,reverse = True)

    if(args["filter"]):
        field, value = args["filter"]
        trials_array = [
            item for item in trials_array
            if item["subject"].get(field) == value
        ]

    if (args['group']):
        trials_array = group_by_field(trials_array, args['group'])
        trials_array.sort(
            key=lambda x: belt_order.index(x['subject_id']) if x['subject_id'] in belt_order else x['subject_id']
        ,reverse = True)

    # Generate set names for the matrix
    set_names = []
    for item in trials_array:
        subj = item['subject']

        if(args['sort'] and not args['group']):
            if(item['index'] == 1):
                set_names.append(f"{item['subject_id']} ({subj[args['sort']]})")
            else:
                set_names.append(f"{item['subject_id']} [{item['index']}] ({subj[args['sort']]})")

        else:
            if(item['index'] == 1):
                set_names.append(f"{item['subject_id']}")
            else:
                set_names.append(f"{item['subject_id']} [{item['index']}]")

    # Analyze Correlations
    if args["split"]:
        plot_correlations_per_sensor(trials_array, set_names, fNIRS_Data['analysis'], column_names, args['save'])
    else:
        plot_correlations(trials_array, set_names, fNIRS_Data['analysis'], args)


if __name__ == "__main__":

    fields = ["age", "skill", "belt", "gender", "handedness"] # Change this to change fields
    parser = argparse.ArgumentParser(
                    description='View correlations between all subjects in a directory')

    parser.add_argument('input_file')
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
    parser.add_argument('--offset', action=argparse.BooleanOptionalAction, default = True, help = 
                        "Parameter to take offset into account, as long as the analyzed data includes it."
                        )

    args = vars(parser.parse_args(sys.argv[1:]))
    main(args)
