#!/bin/bash

#SBATCH -J psb6351_dcm_convert
#SBATCH -o /home/cknowlto/Mattfeld_PSB6351/code/conversion/out_dcm
#SBATCH -e /home/cknowlto/Mattfeld_PSB6351/code/conversion/err_dcm
#SBATCH --qos=normal
#SBATCH --account=acc_gbuzzell
#SBATCH --partition=default-part
#SBATCH --mem=16G
# SET UP A HEUDICONV CALL TO BIDSIFY YOUR DATA
# CAN YOU USE HEUDICONV WITHOUT AN OUTPUT TO HELP ESTABLISH YOUR HEURISTIC FILE?
# Yes by using the -c none and -f convertall flags.
# WHAT WOULD THE FINAL HEUDICONV SUBMISSION LOOK LIKE?
heudiconv -d '/home/cknowlto/Mattfeld_PSB6351/sourcedata2/sourcedata/Mattfeld_REVL-000-vCAT-{subject}-S1/*/*/*/*/*/*' -ss S1 -s '021' -c dcm2niix -f /home/cknowlto/Mattfeld_PSB6351/code/conversion/Mattfeld_PSB6351.py --minmeta -o /home/cknowlto/Mattfeld_PSB6351/dset
