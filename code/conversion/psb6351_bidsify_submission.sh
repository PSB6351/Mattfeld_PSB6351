#!/bin/bash

#SBATCH -J psb6351_dcm_convert
#SBATCH -o /home/cknowlto/Mattfeld_PSB6351/code/conversion/out_dcm
#SBATCH -e /home/cknowlto/Mattfeld_PSB6351/code/conversion/err_dcm
#SBATCH --qos highmem1
#SBATCH --account acc_gbuzzell
#SBATCH --partition default-part
#SBATCH --mem 16G

heudiconv -d '/home/cknowlto/Mattfeld_PSB6351/sourcedata2/sourcedata/Mattfeld_REVL-000-vCAT-{subject}-S1/*/*/*/*/*/*' -b --minmeta -s 021 -c dcm2niix -f /home/cknowlto/Mattfeld_PSB6351/code/conversion/Mattfeld_PSB6351.py -o /home/cknowlto/Mattfeld_PSB6351/dset2
