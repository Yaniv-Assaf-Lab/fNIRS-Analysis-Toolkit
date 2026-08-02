import argparse 
import sys
from pathlib import Path
import pandas as pd
import numpy as np

from lib.load import load_file 
import lib.strings as strings
import lib.models as models

"""
Future Improvements:

- Store a list of labeled subject/trial pairs, and skip labeling existing data.
"""


def main(args):
    # Load metadata
    subject_data = pd.read_csv(args['subject_data'])
    input_folder = Path(args['input_dir'])
    input_files = [str(item) for item in input_folder.iterdir() if item.is_file()]
    file_index = 0 # Outside to count fNIRS data files instead of total files
    for _, file in enumerate(input_files):
        # Load the file
        trial_data = load_file(file, strict = args["strict"])
        if(trial_data.trial_num == -1):
            continue
        file_index += 1
        subject_id = strings.subject_id_from_filename(file)
        subject = subject_data.loc[subject_data['subject_id'] == subject_id]


        # Check for collisions
        if len(subject) > 1:
            offending_id = subject['subject_id'].iloc[0]
            error_msg = f"Subject {offending_id} has more than one instance. Aborting process."
            print(f"{error_msg}")
            raise ValueError(error_msg)
        
        # Label the data
        trial_data.hydrate_subject_data(subject)
        np.savez(f"{args['output_dir']}/labeled{file_index:04d}.npz", trial_data=trial_data)
        

    print(f"Labeled {file_index} subjects.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    description='Labeler for fNIRS data')

    parser.add_argument('-i','--input_dir', default="data/raw")
    parser.add_argument('-o','--output_dir', default="data/labeled")
    parser.add_argument('-d','--subject_data', default="data/subjects.csv")
    parser.add_argument('-s','--strict', default = False, action=argparse.BooleanOptionalAction)   
    args = vars(parser.parse_args(sys.argv[1:]))

    main(args)