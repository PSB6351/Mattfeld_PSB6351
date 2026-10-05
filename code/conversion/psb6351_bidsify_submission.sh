#!/bin/bash

#SBATCH -J psb6351_dcm_convert
#SBATCH -o /home/cbeac004/Mattfeld_PSB6351/code/conversion/out_dcm
#SBATCH -e /home/cbeac004/Mattfeld_PSB6351/code/conversion/err_dcm
#SBATCH --qos # WHAT QOS
#SBATCH --account # WHAT ACCOUNT
#SBATCH --partition # WHAT PARITION

# SET UP A HEUDICONV CALL TO BIDSIFY YOUR DATA
# CAN YOU USE HEUDICONV WITHOUT AN OUTPUT TO HELP ESTABLISH YOUR HEURISTIC FILE?
# WHAT WOULD THE FINAL HEUDICONV SUBMISSION LOOK LIKE?
heudiconv -d '/home/cbeac004/Mattfeld_PSB6351/sourcedata/Mattfeld_REVL-000-vCAT-{subject}-S1/*/*/*/*/*/*' -b --minmeta -s 021 -c dcm2niix -f /home/cbeac004/Mattfeld_PSB6351/code/heuristic.py --overwrite -o /home/cbeac004/Mattfeld_PSB6351/dset
