#!/bin/bash

#SBATCH -J psb6351_dcm_convert
#SBATCH -o /scratch/classroom/psb6351/dcarb040/crash/dcm_convert_out
#SBATCH -e /scratch/classroom/psb6351/dcarb040/crash/dcm_convert_err
#SBATCH --qos pq_psb6351
#SBATCH --account acc_psb6351
#SBATCH --partition classroom

#<<<<<<< HEAD
heudiconv -d '/home/dcarb040/Mattfeld_PSB6351/sourcedata/Mattfeld_REVL-000-vCAT-{subject}-S1/*/*/*/*/*/*' -s 021 -c dcm2niix  -f psb6351_heuristic.py -o /home/dcarb040/Mattfeld_PSB6351/dset -b --minmeta
#=======
#heudiconv -d '/home/amattfel/Mattfeld_PSB6351/sourcedata/Mattfeld_REVL-000-vCAT-{subject}-S1/*/*/*/*/*/*' -b --minmeta -s 021 -c dcm2niix -f /home/amattfel/Mattfeld_PSB6351/code/conversion/psb6351_heuristic.py -o /home/amattfel/Mattfeld_PSB6351/dset
#>>>>>>> 47ac7b23076b2ab2edf118a353c13b2e239ef5c4

