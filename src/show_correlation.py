import argparse
import sys
from pathlib import Path
from collections import defaultdict
import numpy as np
import lib.models as models
import lib.strings as strings
import lib.cfg as cfg
import numpy as np
import matplotlib.pyplot as plt


def plot_correlation_matrix(corr_matrix):
    """
    Visualizes a correlation matrix using a heatmap.
    
    Args:
        corr_matrix (np.ndarray): The (N, N) Pearson correlation matrix.
        channel_names (list of str, optional): Names for the sensors/channels.
    """
    
    
    return ax, cbar


def main(args):

    input_folder = Path(args['input_dir'])
    input_files = [str(item) for item in input_folder.iterdir() if item.is_file()]
    for _, file in enumerate(input_files):
        trial_data = np.load(file, allow_pickle=True)["trial_data"].item()
        segments = np.array(trial_data.segments)


        # Assume `segments` is the input array of shape (R, T, N)
        # 1. Collapse the repetition axis by averaging across all trials
        averaged = np.mean(segments, axis=0)          # Shape: (T, N)

        # 2. Transpose so each row represents a single channel's time series
        channels_over_time = averaged.T                # Shape: (N, T)

        # 3. Compute the full pairwise Pearson correlation matrix
        corr_matrix = np.corrcoef(channels_over_time)  # Shape: (N, N)

        # 1. Initialize the canvas and axis
        fig, ax = plt.subplots(figsize=(8, 8))
        
        # 2. The Heatmap Ritual
        # vmin/vmax are locked to -1 and 1 to ensure consistent coloring across different datasets
        im = ax.imshow(corr_matrix, cmap='RdYlGn', aspect='equal', vmin=-1, vmax=1)
        
        # 'RdYlBu_r' is Red-Yellow-Blue reversed (Red for positive, Blue for negative). 
        # The '_r' suffix is essential here.

        # 3. Add the Color Bar (The Scale of Values)
        cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label('Pearson Correlation Coefficient')

        # 4. Ticks and Labels
        num_channels = corr_matrix.shape[0]
        
        ch_count = 8 if cfg.DIFF_MODE else 16
        labels = [strings.column_names(i, ch_count) for i in range(ch_count)]

        ax.set_xticks(np.arange(len(labels)))
        ax.set_yticks(np.arange(len(labels)))
        
        # Rotate x-axis labels so they don't overlap on the page
        ax.set_xticklabels(labels, rotation=45, ha="right") 
        ax.set_yticklabels(labels)

        # 5. Text Annotations (Optional but recommended for small matrices)
        # We draw a rectangle around each number and place the value inside
        threshold = 0.8  # Threshold to change text color for readability
        for i in range(num_channels):
            for j in range(num_channels):
                val = corr_matrix[i, j]
                color_text = "white" if abs(val) > threshold else "black"
                ax.text(j, i, f"{val:.2f}", ha="center", va="center", 
                        color=color_text, fontsize=10)

        # Adjust layout to prevent clipping of labels
        fig.tight_layout()
        
        # Title with a bit of flair
        plt.title(trial_data.id)
        plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    description='Template generator for data comparisons')

    parser.add_argument('-i','--input_dir', default="data/templates")
    args = vars(parser.parse_args(sys.argv[1:]))

    main(args)