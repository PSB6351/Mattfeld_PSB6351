#!/bin/bash

#SBATCH -J psb6351_dcm_convert
#SBATCH -o /home/umcca001/Mattfeld_PSB6351/code/conversion/out_dcm
#SBATCH -e /home/umcca001/Mattfeld_PSB6351/code/conversion/err_dcm

#SBATCH --partition=default-part

module load miniconda3/24.7.1-none-none-mjgmhio
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate /home/umcca001/Mattfeld_PSB6351/code/psb6351_environment

heudiconv \
-d '/home/umcca001/Mattfeld_PSB6351/sourcedata/Mattfeld_REVL-000-vCAT-{subject}-S1/*/*/*/*/*/*' \
-b \
--minmeta \
-s 021 \
-c dcm2niix \
-f /home/umcca001/Mattfeld_PSB6351/code/conversion/heuristic.py \
-o /home/umcca001/Mattfeld_PSB6351/dset