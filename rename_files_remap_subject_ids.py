#!/usr/bin/env python3
__author__ = "Fredrik Boulund"
__date__ = "2017"
__doc__ = """Rename sample files according to remap table.""" 


from sys import argv, exit
from os import path, rename, mkdir
from collections import namedtuple
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
    parser.add_argument("-d", "--dryrun", action="store_false",
            help="Only print planned actions. Don't rename any files [%(default)s].")

    if len(argv) < 2:
        parser.print_help()
        exit(1)

    return parser.parse_args()


def parse_filenames(filenames):
    """Parse filenames.
    Assumes 4 character subject_id and two character visit id (e.g. v1), for a
    total of 7 characters comprising the sample name.
    E.g. 4295_v4_1.fastq.gz and 4295_v4.statsfile.txt.gz.
    """
   
    for fn in filenames:
        dirname, basename = path.split(fn)
        subject_visit = basename[:7]
        visit = basename[5:7]
        yield dirname, basename, subject_visit, visit

 
def read_remap_table(remap_fn):
    """Read remap table into dataframe, return remapping dict.
    """

    df = pd.read_csv(remap_fn, index_col=0)

    return df.to_dict()["correct_id"]


def main(fastq_files, remap_table, outdir, reverse, link, dryrun):
    """Process all filenames and rename files according to remap table.
    """

    files = parse_filenames(fastq_files)
    remap_dict = read_remap_table(remap_table)
    for filename in files:
        subject_visit = filename[2]
        if subject_visit in remap_dict:
            new_subject = str(remap_dict[filename[2]])
            new_fn = new_subject+"_"+filename[3]+filename[1][7:]
            old_fn = path.join(filename[0], filename[1])
            if reverse:
                new_fn, old_fn = old_fn, new_fn
            print(old_fn, " -->", path.join(outdir, new_fn))
            if not dryrun:
                if link:
                    print("ln -s {} {}".format(old_fn, new_fn))
                else:
                    rename(old_fn, path.join(outdir, new_fn))
        else:
            print(filename[1], " --> No change")

if __name__ == "__main__":
    options = parse_args()
    if not path.exists(options.outdir):
        mkdir(options.outdir)
    main(options.FILE, options.remap, options.outdir, options.reverse, options.link, options.dryrun)
