import argparse 
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import hashlib
import os

import lib.cfg as cfg
import lib.strings as strings
import lib.models as models
import lib.filtering as filtering

def get_file_md5(file_path):
    # Open the file in binary read mode ('rb')
    with open(file_path, "rb") as f:
        # Use file_digest to automatically process the file in chunks
        file_hash = hashlib.file_digest(f, "md5")
    return file_hash.hexdigest()


def main(args):
    cfg_hash = get_file_md5(cfg.__file__)
    input_folder = Path(args['inputdir'])
    input_files = [str(item) for item in input_folder.iterdir() if item.is_file()]
    file_index = 0 # Outside of for loop for real analysis count rather than file count
    for _, file in enumerate(input_files):
        # Check if we already analyzed this one
        output_filename = f"{args['outputdir']}/analyzed{file_index:04d}.npz"
        if(os.path.isfile(output_filename) and not args['force']):
            output_trial = np.load(output_filename, allow_pickle=True)["trial_data"].item()
            if(output_trial.analysis_hash == cfg_hash):
                continue
        
        # If not, perform analysis
        trial_data = np.load(file, allow_pickle=True)["trial_data"].item()
        if(cfg.DIFF_MODE):
            filtering.subtract_channels(trial_data)
        filtering.apply_filtering(trial_data, cfg.FILT_WINDOW_SIZE, cfg.FILT_NOTCH_FREQ, cfg.FILT_NOTCH_Q)
        filtering.extract_segments(trial_data)
        filtering.cut_segments(trial_data)
        trial_data.analysis_hash = cfg_hash
        np.savez(output_filename, trial_data=trial_data)
        file_index += 1

    print(f"Analyzed and filtered {file_index} subjects.")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    description='Analyzer for fNIRS data')

    parser.add_argument('-i','--inputdir', default="data/labeled")
    parser.add_argument('-o','--outputdir', default="data/analyzed")
    parser.add_argument('-f', '--force', action=argparse.BooleanOptionalAction, default=True)
    args = vars(parser.parse_args(sys.argv[1:]))

    main(args)