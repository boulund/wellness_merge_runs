#!/usr/bin/env python3
__author__ = "Fredrik Boulund"
__date__ = "2017"
__doc__ = """Merge sequencing runs to form complete samples.""" 


from sys import argv, exit
from os import path
from collections import namedtuple
import argparse

import pandas as pd


def parse_args():
    """Parse commandline arguments.
    """

    desc = __doc__+". ".join([__date__, __author__])
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument("FASTQ", nargs="+", 
            help="FASTQ files to process.")
    parser.add_argument("-s", "--sample-table", dest="sample_table",
            required=True,
            help="Sample database connecting barcode to individual and visit")
    parser.add_argument("-o", "--outdir", 
            default="merged_runs",
            help="Output directory to write merged files to.")

    if len(argv) < 2:
        parser.print_help()
        exit(1)

    return parser.parse_args()


def parse_filenames(filenames):
    """Parse filenames.

    Yields Fastq_file namedtuples.
    """
   
    Fastq_file = namedtuple("FASTQ_file", "filename barcode lane date flowcell index read")

    for fn in filenames:
        basename = path.basename(fn)
        try:
            _, barcode, lane, date, flowcell, _, index, read = basename.split("_")
        except ValueError:
            print("ERROR: cannot split %s", basename)
        yield Fastq_file(fn, int(barcode), int(lane), date, flowcell, index, int(read[0]))


def read_sample_table(table_fn):
    """Read sample table into dataframe.

    Returns only 'Faeces' samples.
    """

    df = pd.read_table(table_fn, index_col=0)

    return df[df["Sample type"] == "Faeces"]


def create_new_filenames(files, samples):
    """Identify what subject and visit each barcoded file corresponds to and create new filenames accordingly.

    Yields tuples of (old_filename, new_filename).
    """
    for fastq_file in files:
        subject_id, visit = samples.loc[fastq_file.barcode, ["Subject id", "Visit"]]
        visit_clean = visit[-1] 
        yield fastq_file.filename, str(subject_id)+"_v"+str(visit_clean)+"_"+str(fastq_file.read)+".fastq.gz"

def main(fastq_files, sample_table, outdir):
    """Process all filenames to determine what sample each file belongs to 
    and generate file merge commands.
    """

    files = list(parse_filenames(fastq_files))
    samples = read_sample_table(sample_table)
    new_filenames = create_new_filenames(files, samples)

    for old, new in new_filenames:
        print(f"cat {old} >> {outdir}/{new}")
    

if __name__ == "__main__":
    options = parse_args()
    main(options.FASTQ, options.sample_table, options.outdir)
