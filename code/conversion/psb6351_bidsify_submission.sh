#!/bin/bash

#SBATCH -J psb6351_dcm_convert
#SBATCH -o /home/mali092/Mattfeld_PSB6351/code/conversion/out_dcm
#SBATCH -e /home/mali092/Mattfeld_PSB6351/code/conversion/err_dcm
#SBATCH --qos classroom
#SBATCH --account acc_psb6351
#SBATCH --partition default-part

# SET UP A HEUDICONV CALL TO BIDSIFY YOUR DATA
# CAN YOU USE HEUDICONV WITHOUT AN OUTPUT TO HELP ESTABLISH YOUR HEURISTIC FILE?
# WHAT WOULD THE FINAL HEUDICONV SUBMISSION LOOK LIKE?
heudiconv -d '/home/mali092/Mattfeld_PSB6351/sourcedata/Mattfeld_REVL-000-vCAT-{subject}-S1/*/*/*/*/*/*' -s 021 -ss S1 -f /home/mali092/Mattfeld_PSB6351/code/conversion/Mattfeld_PSB6351.py -c dcm2niix -o /home/mali092/Mattfeld_PSB6351/dset -b
