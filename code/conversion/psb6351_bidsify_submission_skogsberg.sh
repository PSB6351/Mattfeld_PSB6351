#!/bin/bash

#SBATCH -J psb6351_dcm_convert
#SBATCH -o /home/eskog001/Mattfeld_PSB6351_eas/code/conversion/out_dcm
#SBATCH -e /home/eskog001/Mattfeld_PSB6351_eas/code/conversion/err_dcm
#SBATCH --qos=classroom
#SBATCH --account=acc_psb6351
##SBATCH --partition=

# SET UP A HEUDICONV CALL TO BIDSIFY YOUR DATA
# CAN YOU USE HEUDICONV WITHOUT AN OUTPUT TO HELP ESTABLISH YOUR HEURISTIC FILE?
## yes. using `-f convertall -c none`

# WHAT WOULD THE FINAL HEUDICONV SUBMISSION LOOK LIKE?
## final submission:
heudiconv \
    -d '/home/eskog001/Mattfeld_PSB6351_eas/sourcedata/sub-021_extracted/Mattfeld_REVL-000-vCAT-{subject}-S1/*/*/*/*/*/>
    -s 021 \
    -f /home/eskog001/Mattfeld_PSB6351_eas/code/Mattfeld_PSB6351.py \
    -c dcm2niix \
    -b \
    --minmeta \
    -o /home/eskog001/Mattfeld_PSB6351_eas/dset