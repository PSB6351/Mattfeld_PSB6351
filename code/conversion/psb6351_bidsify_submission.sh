#!/bin/bash

#SBATCH -J psb6351_dcm_convert
#SBATCH -o /home/amattfel/Mattfeld_PSB6351/code/conversion/out_dcm
#SBATCH -e /home/amattfel/Mattfeld_PSB6351/code/conversion/err_dcm
#SBATCH --qos pq_madlab
#SBATCH --account iacc_madlab
#SBATCH --partition 16C_128G

heudiconv -d '/home/amattfel/Mattfeld_PSB6351/sourcedata/Mattfeld_REVL-000-vCAT-{subject}-S1/*/*/*/*/*/*' -b --minmeta -s 021 -c dcm2niix -f /home/amattfel/Mattfeld_PSB6351/code/conversion/Mattfeld_PSB6351.py -o /home/amattfel/Mattfeld_PSB6351/dset2
