# YALab's specialized fNIRS analysis Toolkit

This toolkit was made to easily and programmatically analyze the data from our fNIRS measurements.
We take a repetitive measurement, in which each repetition is marked by an event, such that any time between 2 events is a repetition.
This toolkit has several features:
- Analysis
- Graphing
- Correlation
- Viewing and editing

## Initial Setup

In order to use this toolkit, you must first create a `subjects.py` file which includes your subjects in the following format:
```
subjects = {
    "SUBJECT_ID": {"age": <age>, "skill": <skill>, "belt": <belt>, "gender": <gender>, "handedness": <handedness>},
    ...
}
```

These are fields that are useful for our research specifically, but you are welcome to fork this project and modify them however you like, as it is not very difficult.

Then, you will need a directory (set up as `data` in the makefile) which holds the subject's fNIRS data, in the Artinis OxySoft XML format, or a `.snirf` format. The file names for these must be in the following format:

```
<SUBJECT_ID>_<TRIAL>.snirf/.xml
```

Then, make sure the parameters in the makefile are satisfactory, install all of the Python libraries required to run the tools, and analyze to your heart's content.

## Analysis

The analysis tool takes in files using a named format for each subject, cross references them with a subject's data in the file `subjects.py`, and outputs `.npz` files which include the subject's parameters. The tool also uses the `filtering.py` library to filter the data in a desired way before exporting.

### Usage

Executing `./analyze.py -h` (or `python analyze.py -h`) shows the help text detailing the exact parameters of the program and what they do.

```
usage: analyze.py [-h] [-m mode] [-f factor] [-w length] [-b freqeuncy q_factor] input_dir output_dir

Analyzer for fNIRS data

positional arguments:
  input_dir
  output_dir

options:
  -h, --help            show this help message and exit
  -m mode, --mode mode  Selects the differential analysis mode. Choosing "subtract" will subtract the O2Hb and HHb channels, and "divide" will divide them.
  -f factor, --factor factor
                        If the "subtract" mode is selected, this parameter controls the factor by which the HHb channel is multiplied. Default is a normalization to the standard deviation of the O2Hb signal.
  -w length, --window length
                        This parameter adds a moving window average, with variable length.
  -b freqeuncy q_factor, --bandgap freqeuncy q_factor
                        These 2 parameters control a band-gap (also called band-stop) filter to the data, mostly for heart beat mitigation.
```


## Graphing

After analysis, the toolkit includes a tool for graphing a specific subject, for more pinpoint analysis. It can also save the plot as an image, in order to easily send the results to people.

### Usage
```
usage: graph.py [-h] [-o OUTPUT_DIR] file_path

Visualize a specific analyzed .npz file.

positional arguments:
  file_path             Path to the .npz data file

options:
  -h, --help            show this help message and exit
  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        Directory to save the plot
```


## Correlation

The toolkit also includes a tool for viewing the correlations between subject's measurements. The tool calculates the average correlations between all test subjects and arranges them in a matrix, which can be filtered and sorted with any parameter of your choosing, taken from the `subjects.py` dictionary. 


### Usage

```
usage: correlate.py [-h] [-s sort] [-f field value] [-p | --split | --no-split] [-a save_dir] input_dir

View correlations between all subjects in a directory

positional arguments:
  input_dir

options:
  -h, --help            show this help message and exit
  -s sort, --sort sort  Allows sorting by a specified parameter
  -f field value, --filter field value
                        Allows filtering by a specified field and value
  -p, --split, --no-split
                        Normally the correlation is averaged between all channels, in order to create one correlation matrix. Enabling this option allows for the creation of separate correlation matrices, one for each sensor channel.
  -a save_dir, --save save_dir
                        Allows saving of the resulting matrix to an image.
```


## Viewing and Editing

The toolkit allows for manual editing and viewing of raw .snirf files. This is achieved by the `snirf-edit.py` and `view.py` scripts. These are very hacked together though, and unfinished, so currently we will not elaborate too much, and encourage you to use at your own risk.