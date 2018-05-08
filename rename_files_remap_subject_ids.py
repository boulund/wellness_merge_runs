#!/usr/bin/env python3
__author__ = "Fredrik Boulund"
__date__ = "2017"
__doc__ = """Rename V4 sample files according to remap table.""" 
__version__ = "0.1.1"


from sys import argv, exit
from os import path, mkdir
from collections import namedtuple
import shutil
import argparse

import pandas as pd


def parse_args():
    """Parse commandline arguments.
    """

    desc = __doc__+". ".join([__date__, __author__])
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument("FILE", nargs="+", 
            help="FILEs to process.")
    parser.add_argument("-r", "--remap", 
            help="CSV with subject IDs to remap. Three columns: subject_visit, subject_incorrect, subject_correct")
    parser.add_argument("-o", "--outdir", required=True,
            help="output dir for all renamed files (required to avoid collisions during renaming).")
    parser.add_argument("--reverse", action="store_true",
            help="Reverse the mapping [%(default)s].")
    parser.add_argument("-l", "--link", action="store_true",
            help="Create symlinks instead of copying [%(default)s].")
    parser.add_argument("--execute", action="store_true",
            help="Actually execute file system actions. Default is to only print planned actions [%(default)s].")

    if len(argv) < 2:
        parser.print_help()
        exit(1)

    return parser.parse_args()


def parse_filenames(filenames):
    """Parse filenames.

    The sample filenames are typically:

        1.3250.V3_S34_L001_R1_001.fastq.gz

    The first digit (1) is the same for all file names. 
    The second part is the sample name (3250).
    The third part is the visit (V3). 
        NOTE: This is not present for v1 samples!!:
        1.3264_S67_L001_R1_001.fastq.gz
        Here it is missing, and no dot follows the sample name.
    We are only interested in renaming V4 samples here anyway, so not an issue.
    """
   
    for fn in filenames:
        dirname, basename = path.split(fn)
        try:
            _, subject, visit = basename[:9].split(".")
            subject = subject
            if visit.startswith("fi"):
                # Visit one files have no visit in filename!
                visit = "V1"
        except ValueError:
            # This happens when there is no visit in the filename (i.e. visit1)
            subject = basename[2:6]
            visit = "V1"
        try:
            yield dirname, basename, int(subject), visit
        except ValueError:
            print("WARNING: Could not parse filename", fn, " -- Ignoring")

 
def read_remap_table(remap_fn, reverse):
    """Read remap table into dataframe, return remapping dict.
    """

    df = pd.read_csv(remap_fn, index_col=0)
    d = df.to_dict()["ind.ratt"]
    if reverse:
        d = {str(v)+k[-3:]: k[0:4] for k, v in d.items()}
    return d


def main(fastq_files, remap_table, outdir, reverse, link, execute):
    """Process all filenames and copy files to new filenames according to remap table.
    """

    files = parse_filenames(fastq_files)
    remap_dict = read_remap_table(remap_table, reverse)
    for filename in files:
        subject = filename[2]
        visit = filename[3]
        subject_visit = "{}_{}".format(subject, visit.lower())
        if subject_visit in remap_dict:
            new_subject = str(remap_dict[subject_visit])
            new_fn = filename[1][:2]+new_subject+filename[1][6:]
            old_fn = path.join(filename[0], filename[1])
            print(old_fn, " -->", path.join(outdir, new_fn))
            if execute:
                if link:
                    print("ln -s {} {}".format(old_fn, new_fn))
                else:
                    shutil.copy(old_fn, path.join(outdir, new_fn))
        else:
            print(path.join(filename[0], filename[1]), " --> No change")

if __name__ == "__main__":
    options = parse_args()
    if not path.exists(options.outdir):
        mkdir(options.outdir)
    main(options.FILE, options.remap, options.outdir, options.reverse, options.link, options.execute)
