#!/bin/bash

#SBATCH -J psb6351_dcm_convert
#SBATCH -o /home/sfrai003/Mattfeld_PSB6351/code/conversion/out_dcm
#SBATCH -e /home/sfrai003/Mattfeld_PSB6351/code/conversion/err_dcm
#SBATCH --qos highmem1
#SBATCH --account acc_madlab
#SBATCH --partition highmem1-sapphirerapids

# SET UP A HEUDICONV CALL TO BIDSIFY YOUR DATA

# CAN YOU USE HEUDICONV WITHOUT AN OUTPUT TO HELP ESTABLISH YOUR HEURISTIC FILE?
# ---> Yes! See below for the dry run. Most important flags: -c and -f
#heudiconv -d '/home/sfrai003/Mattfeld_PSB6351/sourcedata/Mattfeld_REVL-000-vCAT-{subject}-S1/*/*/*/*/*/*' -b --minmeta -s 021 -c none -f convertall -o /home/sfrai003/Mattfeld_PSB6351/dset

# WHAT WOULD THE FINAL HEUDICONV SUBMISSION LOOK LIKE?
heudiconv -d '/home/sfrai003/Mattfeld_PSB6351/sourcedata/Mattfeld_REVL-000-vCAT-{subject}-S1/*/*/*/*/*/*' -b --minmeta -s 021 -c dcm2niix -f /home/sfrai003/Mattfeld_PSB6351/code/conversion/Mattfeld_PSB6351.py -o /home/sfrai003/Mattfeld_PSB6351/dset
