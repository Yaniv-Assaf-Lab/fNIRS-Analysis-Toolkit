#!/usr/bin/python
import sys
import os
import numpy as np
from pathlib import Path
from load import load_file
from filtering import *
from subjects import subjects
import argparse

def main(args):


    fNIRS_Data = {
        "trials": [],
        "column_names": [],
        "analysis": {
            "transform": args["transform"],
            "factor": args["factor"],
            "filters": [args["window"], args["bandgap"]],
            "phase_locked": False
        }
    }
        
    # Build file list
    output_dir = os.path.dirname(args["output_file"])
    file_paths = []
    with os.scandir(args["input_dir"]) as dir:
        for entry in dir:
            if entry.is_file():
                file_paths.append(os.path.join(args["input_dir"], entry.name))

    # Load old data if exists
    fNIRS_Data_old = None
    if(os.path.isfile(args["output_file"])):
        fNIRS_Data_old = np.load(args["output_file"], allow_pickle=True)['fNIRS_Data'].item()
    else:
        print("No old data found. Recreating entire database.")

    # Find template file and use it
    template_file = (args["template_file"]) if (args.get('template_file', False)) else (os.path.join(output_dir, "template.npz"))
    template = None
    try:
        template = np.load(template_file, allow_pickle=True)['stacks']
    except:
        print("Template not found. Defaulting to 0 offset.")
    
    if (template is not None):
        fNIRS_Data['analysis']['phase_locked'] = True
    
    old_valid = fNIRS_Data_old and fNIRS_Data_old['analysis'] == fNIRS_Data['analysis']
    for i, f in enumerate(file_paths):
        file_stem = Path(f).stem
        subject_id = file_stem.split(sep = " ")[0]
        trial_idx = 1
        if (file_stem.split()[-1].isnumeric() and len(file_stem.split()) != 1):
            trial_idx = int(file_stem.split()[-1])


        

        if (old_valid):
            old_trial = next((t for t in fNIRS_Data_old.get('trials', []) 
                if t.get('subject_id') == subject_id and t.get('index') == trial_idx), None)

            if(old_trial):
                print(f'Subject "{subject_id}" already analyzed, skipping... ({i + 1}/{len(file_paths)})')
                fNIRS_Data['trials'].append(old_trial)
                continue        
                                 
        df, marker_indices, column_names, sample_rate = load_file(f)
        if sample_rate == 0:
            continue

        subject = subjects.get(subject_id, 0)
        trial = {
            "subject_id": subject_id,
            "subject": subject,
            "index": trial_idx,
            "stacks": [],
            "separate_stacks": [],
            "offset": 0
        }

        df = apply_filtering(df, args["window"], sample_rate, args["bandgap"][0], args["bandgap"][1])

        segments = extract_segments(df, marker_indices)
        trial['separate_stacks'] = retime_segments(segments)
        
        # Setup parameters (runs only for the first subject loaded)
        if(i == 0):
            if(fNIRS_Data['analysis']["transform"] != None):
                fNIRS_Data['column_names'] = [(column[:-4]) for column in column_names[::2]]
            else:
                fNIRS_Data['column_names'] = column_names
        
        if (fNIRS_Data['analysis']['transform'] == "subtract"):
            subtract_channels(segments, args["factor"])
        if (fNIRS_Data['analysis']['transform'] == "divide"):
            divide_channels(segments)
        
        if(fNIRS_Data['analysis']['phase_locked']):
            offsets = []
            # for j, stack in enumerate(trial['separate_stacks'][::2]): # HbO Only
            for j, stack in enumerate(trial['separate_stacks']): # HbO Only
                stack_t = np.transpose(stack)
                for _, run in enumerate(stack_t):
                    offsets.append(find_offset_limited(template[::,j], run, len(stack) / 5))
            trial['offset'] = np.mean(np.array(offsets)) 
            print(f"Mean offset: {np.mean(np.array(offsets))}, Median offset: {np.median(np.array(offsets))}, Delta offset: {np.mean(np.array(offsets)) - np.median(np.array(offsets))}")
        
        trial['stacks'] = retime_segments(segments)
        fNIRS_Data['trials'].append(trial)
        # print(f"fNIRS Trials shape: {fNIRS_Data['trials'].shape}")
        print(f"Analyzed subject \"{subject_id}\" ({i + 1}/{len(file_paths)})")
        
    os.makedirs(output_dir, exist_ok=True)
    np.savez(args['output_file'], fNIRS_Data = fNIRS_Data)
    print(f"Saved results into file: {args['output_file']}")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    description='Analyzer for fNIRS data')

    parser.add_argument('input_dir')
    parser.add_argument('output_file')
    parser.add_argument('-t', '--transform', metavar = 'transform', required = False, choices = ['subtract', 'divide'], help = 
                        "Selects the differential analysis transform mode. Choosing \"subtract\" will subtract the O2Hb and HHb channels, and \"divide\" will divide them."
                        )
    parser.add_argument('-m', '--template', metavar = 'template_file', required = False, help = 
                        "TODO"
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
