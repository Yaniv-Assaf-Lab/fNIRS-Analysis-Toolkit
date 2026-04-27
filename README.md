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

These are fields that are useful for our research specifically, but you are welcome to fork this project and modify them however you like, with full instructions [below](#modifying-fields).

Then, you will need a directory (set up as `data` in the makefile) which holds the subject's fNIRS data, in the Artinis OxySoft XML format, or a `.snirf` format. The file names for these must be in the following format:

```
<SUBJECT_ID> <TRIAL>.snirf/.xml
```
Please note that `SUBJECT_ID` may not contain spaces.
Then, make sure the parameters in the makefile are satisfactory, install all of the Python libraries required to run the tools, and analyze to your heart's content.

Note that on some Linux systems (e.g., Ubuntu with Wayland), you may need to set the `QT_QPA_PLATFORM` environment variable to wayland:
```
export QT_QPA_PLATFORM=wayland
```

## Analysis

The analysis tool takes in files using a named format for each subject, cross references them with a subject's data in the file `subjects.py`, and output one `.npz` file which include the subject's parameters. The tool also uses the `filtering.py` library to filter the data in a desired way before exporting.

### Usage

Execute `./analyze.py -h` (or `python analyze.py -h`) in order to get usage information and help.

## Template Generation

The template generation tool (`template.py`) takes an already analyzed `.npz` dataset and computes a generalized mean template across all subjects and trials. This template can then be fed back into the analysis tool to calculate alignment offsets (phase-locking) for future graphing and correlation.

### Usage

Execute `./template.py -h` (or `python template.py -h`) in order to get usage information and help.

## Graphing

After analysis, the toolkit includes a tool for graphing a specific subject, for more pinpoint analysis. It can also save the plot as an image, in order to easily send the results to people.

### Usage
Execute `./graph.py -h` (or `python graph.py -h`) in order to get usage information and help.


## Correlation

The toolkit also includes a tool for viewing the correlations between subject's measurements. The tool calculates the average correlations between all test subjects and arranges them in a matrix, which can be filtered and sorted with any parameter of your choosing, taken from the `subjects.py` dictionary. 


### Usage

Execute `./correlate.py -h` (or `python correlate.py -h`) in order to get usage information and help.


## Viewing and Editing

The toolkit allows for manual editing and viewing of raw .snirf files. This is achieved by the `snirf-edit.py` and `view.py` scripts. These are very hacked together though, and unfinished, so currently we will not elaborate too much, and encourage you to use at your own risk.


## Makefile Usage

This project includes a Makefile to simplify running common tasks such as analysis, graphing, and correlation.

### Configuration Variables

At the top of the Makefile, you can configure the following:

- `RAW_DIR`: Directory containing raw `.snirf` and Artinis OxySoft `.xml` files  
- `ANALYZED_DIR`: Output directory for processed `.npz` files  
- `IMG_DIR`: Directory where generated graphs/images will be saved  
- `ANALYZE_OPTIONS`: Additional flags passed to `analyze.py`  
- `PARALLEL`: Number of parallel processes (`0` = use all available cores)  


### Available Commands

#### Full Pipeline

To start from a clean slate, and reach the correlation chart, simply run
```
make
```
And wait for the correlation window to show up (Yup, that's it).

#### Analyze Data
To run the full analysis pipeline on all raw files:
```
make analyze
```

With transformations:
```
make analyze-sub     # subtraction transform
make analyze-div     # division transform
```


#### Graphing

Generate graphs for all analyzed files:
```
make graph
```

Save graphs as image files:
```
make save-graphs
```


#### Correlation

Compute correlations across all subjects:
```
make correlate
```

Split correlations into groups and save images:
```
make correlate-split
```

Filter correlations by belt level:
```
make correlate-blck     # black belt
make correlate-brwn     # brown belt
make correlate-prpl     # purple belt
make correlate-blue     # blue belt
make correlate-whte     # white belt
```



#### Editing / Viewing

Open a file for viewing and manual editing:
```
make edit FILE="path/to/file"
```


#### Cleanup

Remove all analyzed output files:
```
make clean
```

## Modifying fields

In order to add/remove fields from this analysis toolkit for your own use, follow these instructions:

1. Make sure all the subjects in `subjects.py` have all the fields needed. For subjects who did not fill a specific field, add an "unknown" value instead of leaving it empty.
2. In the file `correlate.py`, under the `__main__` check, find the array `fields` and make sure the fields there are set to the fields you will need to sort, filter, or group by.
3. Run your analysis to your heart's content. 