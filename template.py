#!/usr/bin/python

import sys
import os
import numpy as np
import argparse
import matplotlib.pyplot as plt


def main(args):

    fNIRS_Data = None
    if(os.path.isfile(args["input_file"])):
        fNIRS_Data = np.load(args["input_file"], allow_pickle=True)['fNIRS_Data'].item()
    else:
        print("The input file does not exist! Exiting...")
        exit(1)

                
    # Use a list to store objects containing (skill, stack, name)
    big_stack_mean = []
    # big_stack_median = []
    analysis = fNIRS_Data['analysis']
    column_names = fNIRS_Data['column_names']
    # 1. Process all files
    # print(f"fNIRS Data: {fNIRS_Data}")
    for trial in fNIRS_Data['trials']:
        stacks = trial["separate_stacks"]
        subject = trial["subject"]
        subject_id = trial['subject_id']
        

        if(subject == 0):
            print(f"Subject not found: {f}")
            exit(1)

        # Normalize
        mins = np.min(stacks, axis=1, keepdims=True)
        maxs = np.max(stacks, axis=1, keepdims=True)
        stacks = (stacks - mins) / (maxs - mins)
        stacks_mean = np.mean(stacks, axis=0)
        # big_stack_mean.append(stacks_mean[::, ::2]) # HbO Only
        big_stack_mean.append(stacks_mean)

    big_stack_mean = np.mean(big_stack_mean, axis=0)
    print(f"Generated template with shape: {big_stack_mean.shape}")
    
    if(args['show']):
        target_len = big_stack_mean.shape[0]
        num_sensors = big_stack_mean.shape[1]
        time = np.linspace(0, 1, target_len)
        
        fig, axes = plt.subplots(4, 2, figsize=(12, 13), sharex=True)
        axes = axes.flatten()

        main_title = "Template result"
        fig.suptitle(main_title, fontsize=14, y=0.98)
        
        fig.canvas.manager.set_window_title(f"Template result")
        for i in range(8):
            ax = axes[i]
            
            colors = ["#d62728", "#1f77b4"] # Strong Red and Blue
            labels = ["hbo", "hbr"]
            
            for j in range(2):
                sensor_idx = i * 2 + j
                if (sensor_idx < num_sensors):
                    ax.plot(time, big_stack_mean.transpose()[sensor_idx], label=labels[j], color=colors[j], linewidth=1.2)
            
            title_idx = i * 2
            if(len(column_names)) == 16:
                column_names = column_names[::2]
            ax.set_title(f"Channel {i+1}: {column_names[i]}", fontsize=10)

            ax.set_ylabel(r"Norm. $\Delta$ Intensity")
            ax.grid(True, linestyle='--', alpha=0.4)
            ax.legend(fontsize="small", loc="upper right")
        plt.xlabel("Normalized Trial Duration (0% → 100%)", fontsize=11)
        plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # Adjust layout to make room for suptitle
        plt.show()
    else:
        np.savez(args["output_file"], 
                stacks = big_stack_mean, 
                analysis = analysis,
                subject = None,)






if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    description='Analyzer for fNIRS data')

    parser.add_argument('input_file')
    parser.add_argument('output_file')
    parser.add_argument('-s', '--show', action=argparse.BooleanOptionalAction, default = False, help = 
                        "Shot the output template")
    args = vars(parser.parse_args(sys.argv[1:]))

    main(args)
