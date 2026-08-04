import argparse
import sys
from pathlib import Path
from collections import defaultdict
import numpy as np
import lib.models as models

def get_class_by_name(class_name):
    match class_name:
        case "subject_belt":
            return models.Belt
        case "subject_gender":
            return models.Gender
        case "subject_handedness":
            return models.Handedness
        case _: # The underscore (_) acts as the default case
            print("Good job, you broke something. This error message should never show up.")
            exit(1)


def main(args):

    input_folder = Path(args['input_dir'])
    input_files = [item for item in input_folder.iterdir() if item.is_file()]
    filter_members = set(get_class_by_name(args['parameter']))
    
    # Key: Member ID, Value: List of file paths
    member_to_files = defaultdict(list)

    for file_path in input_files:
        fnirs_trial = np.load(file_path, allow_pickle=True)["trial_data"].item()
        parameter_value = getattr(fnirs_trial, args['parameter'])

        if parameter_value in filter_members:
            member_to_files[parameter_value].append(file_path)

    # Now we iterate through the members and immediately access their files.
    for member in filter_members:
        # Initialize the template
        output_filename = f"{args['output_dir']}/template_{member}.npz"
        template = models.fNIRSTrial()
        template.id = f"{args['parameter']} = {member}" 

        
        # Fill in the template
        assigned_files = member_to_files.get(member, [])
        for file_path in assigned_files:
            fnirs_trial = np.load(file_path, allow_pickle=True)["trial_data"].item()
            template.segments.extend(fnirs_trial.segments)
        
        np.savez(output_filename, trial_data=template)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    description='Template generator for data comparisons')

    parser.add_argument('-i','--input_dir', default="data/analyzed")
    parser.add_argument('-o','--output_dir', default="data/templates")
    parser.add_argument('-p', '--parameter', choices=["subject_belt", "subject_gender", "subject_handedness"], default="subject_belt")
    args = vars(parser.parse_args(sys.argv[1:]))

    main(args)