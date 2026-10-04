#!/bin/bash

#SBATCH -J psb6351_dcm_convert
#SBATCH -o /home/aoste011/Mattfeld_PSB6351/code/conversion/out_dcm
#SBATCH -e /home/aoste011/Mattfeld_PSB6351/code/conversion/err_dcm
#SBATCH --qos=classroom
#SBATCH --account=acc_psb6351
#SBATCH --mem=16G

# SET UP A HEUDICONV CALL TO BIDSIFY YOUR DATA

# CAN YOU USE HEUDICONV WITHOUT AN OUTPUT TO HELP ESTABLISH YOUR HEURISTIC FILE?
# Yes: running heudiconv with "-c none -f convertall" converts nothing, but it creates
# dset/.heudiconv/021/info/dicominfo.tsv, which lists every scan's name and dimensions
# so you can write the heuristic file.

# WHAT WOULD THE FINAL HEUDICONV SUBMISSION LOOK LIKE?
rm -rf /home/aoste011/Mattfeld_PSB6351/dset/.heudiconv/021

heudiconv -d "/home/aoste011/Mattfeld_PSB6351/sourcedata/Mattfeld_REVL-000-vCAT-{subject}-S1/*/*/*/*/*/*" \
    -s 021 \
    -f /home/aoste011/Mattfeld_PSB6351/code/conversion/Mattfeld_PSB6351.py \
    -c dcm2niix \
    -b \
    --minmeta \
    --overwrite \
    -o /home/aoste011/Mattfeld_PSB6351/dset
