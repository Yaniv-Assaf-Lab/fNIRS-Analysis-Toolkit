import argparse 
import sys
import pandas as pd
from lib.load import load_file 

def main(args):
    subject_data = pd.read_csv(args['subject_data'])
    print(subject_data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    description='Labeler for fNIRS data')

    parser.add_argument('-i','--input_dir', default="data/raw")
    parser.add_argument('-o','--output_dir', default="data/labeled")
    parser.add_argument('-d','--subject_data', default="data/subjects.csv")
    parser.add_argument('-s','--strict', default = False, action=argparse.BooleanOptionalAction)   
    args = vars(parser.parse_args(sys.argv[1:]))

    main(args)