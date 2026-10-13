#!/bin/bash

#SBATCH -J psb6351_dcm_convert
<<<<<<< HEAD
#SBATCH -o /home/mali092/Mattfeld_PSB6351/code/conversion/out_dcm
#SBATCH -e /home/mali092/Mattfeld_PSB6351/code/conversion/err_dcm
#SBATCH --qos classroom
#SBATCH --account acc_psb6351
#SBATCH --partition default-part

# SET UP A HEUDICONV CALL TO BIDSIFY YOUR DATA
# CAN YOU USE HEUDICONV WITHOUT AN OUTPUT TO HELP ESTABLISH YOUR HEURISTIC FILE?
# WHAT WOULD THE FINAL HEUDICONV SUBMISSION LOOK LIKE?
heudiconv -d '/home/mali092/Mattfeld_PSB6351/sourcedata/Mattfeld_REVL-000-vCAT-{subject}-S1/*/*/*/*/*/*' -s 021 -ss S1 -f /home/mali092/Mattfeld_PSB6351/code/conversion/Mattfeld_PSB6351.py -c dcm2niix -o /home/mali092/Mattfeld_PSB6351/dset -b
=======
#SBATCH -o /home/amattfel/Mattfeld_PSB6351/code/conversion/out_dcm
#SBATCH -e /home/amattfel/Mattfeld_PSB6351/code/conversion/err_dcm
#SBATCH --qos pq_madlab
#SBATCH --account iacc_madlab
#SBATCH --partition 16C_128G

heudiconv -d '/home/amattfel/Mattfeld_PSB6351/sourcedata/Mattfeld_REVL-000-vCAT-{subject}-S1/*/*/*/*/*/*' -b --minmeta -s 021 -c dcm2niix -f /home/amattfel/Mattfeld_PSB6351/code/conversion/Mattfeld_PSB6351.py -o /home/amattfel/Mattfeld_PSB6351/dset2
>>>>>>> upstream/main
