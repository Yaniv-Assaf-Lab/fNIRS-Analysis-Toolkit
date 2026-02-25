#!/usr/bin/python
import sys
import os
import numpy as np
from scipy.interpolate import interp1d
from pathlib import Path
from load import load_file
from filtering import apply_filtering, extract_segments, subtract_channels, divide_channels
from subjects import subjects
import argparse


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



def main(args):
    file_paths = []
    with os.scandir(args["input_dir"]) as dir:
        for entry in dir:
            if entry.is_file():
                file_paths.append(os.path.join(args["input_dir"], entry.name))

    # 1. Process all files
    for i, f in enumerate(file_paths):
        
        file_stem = Path(f).stem
        id = file_stem.split(sep = " ")[0]
        trial = 1
        if file_stem.split()[-1].isnumeric():
            trial = file_stem.split()[-1]

        file_name = os.path.join(args["output_dir"], f"{id}_{trial}.npz")
        if(os.path.isfile(file_name)):
            data = np.load(file_name, allow_pickle=True)
            analysis_mode = data["mode"]
            if(analysis_mode == args["mode"]):
                print(f"Subject \"{id}\" already analyzed, skipping... ({i + 1}/{len(file_paths)})")
                continue

                                 
        df, marker_indices, column_names, sample_rate = load_file(f)
        if sample_rate == 0:
            continue
        
        df = apply_filtering(df, args["window"], sample_rate, args["bandgap"][0], args["bandgap"][1])

        segments = extract_segments(df, marker_indices)
        column_names = [column[:9] for column in column_names]
        if (args["mode"] == "subtract"):
            subtract_channels(segments, args["factor"])
            column_names = column_names[::2]
        if (args["mode"] == "divide"):
            column_names = column_names[::2]
            divide_channels(segments)
        
        stacked = normalize_segments(segments)

        # Get first and last words of filename
        
        
        subject = subjects.get(id, 0)
        
        os.makedirs(args["output_dir"], exist_ok=True)
        np.savez(file_name, 
                    stack = stacked, 
                    column_names = column_names,
                    id = id, 
                    mode = args["mode"],
                    subject = subject,
                    trial = trial)
        print(f"Analyzed subject \"{id}\" ({i + 1}/{len(file_paths)})")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    description='Analyzer for fNIRS data')

    parser.add_argument('input_dir')
    parser.add_argument('output_dir')
    parser.add_argument('-m', '--mode', metavar = 'mode', required = False, choices = ['subtract', 'divide'], help = 
                        "Selects the differential analysis mode. Choosing \"subtract\" will subtract the O2Hb and HHb channels, and \"divide\" will divide them."
                        )
    parser.add_argument('-f', '--factor', metavar = 'factor', type=float, help = 
                        "If the \"subtract\" mode is selected, this parameter controls the factor by which the HHb channel is multiplied. Default is a normalization to the standard deviation of the O2Hb signal."
                        )     
    parser.add_argument('-w', '--window', metavar = 'length', type=float, default = 0, help = 
                        "This parameter adds a moving window average, with variable length."
                        )
    parser.add_argument('-b', '--bandgap', nargs = 2, metavar=('freqeuncy', 'q_factor'), type=float, required = False, default = [0, 0], help = 
                        "These 2 parameters control a band-gap (also called band-stop) filter to the data, mostly for heart beat mitigation."
                        )      
    args = vars(parser.parse_args(sys.argv[1:]))

    main(args)
