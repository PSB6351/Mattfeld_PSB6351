#!/bin/bash

#SBATCH -J psb6351_dcm_convert_loc
#SBATCH -o /home/eskog001/Mattfeld_PSB6351_eas/code/conversion/out_dcm_loc
#SBATCH -e /home/eskog001/Mattfeld_PSB6351_eas/code/conversion/err_dcm_loc
#SBATCH --qos=classroom
#SBATCH --account=acc_psb6351
#SBATCH --mem=16G
# NOTE: --mem added due to err in orig script

# LOCALIZER ONLY conversion for my final analysis (V1/V2/ FFA ROI analysis)


heudiconv \
    -d '/home/eskog001/Mattfeld_PSB6351_eas/sourcedata/sub-021_extracted/Mattfeld_REVL-000-vCAT-{subject}-S1/*/*/*/*/*/*.dcm' \
    -s 021 \
    -f /home/eskog001/Mattfeld_PSB6351_eas/code/Mattfeld_PSB6351_loc.py \
    -c dcm2niix \
    -b \
    --minmeta \
    -o /home/eskog001/Mattfeld_PSB6351_eas/dset2

# copy the new files into the main BIDS folder only if both localizer runs converted completely (CHECK)
new=/home/eskog001/Mattfeld_PSB6351_eas/dset2/sub-021
main=/home/eskog001/Mattfeld_PSB6351_eas/dset/sub-021
if [ -f ${new}/func/sub-021_task-loc_run-1_bold.nii.gz ] && [ -f ${new}/func/sub-021_task-loc_run-2_bold.nii.gz ]; then
    mkdir -p ${main}/fmap
    cp -n ${new}/func/sub-021_task-loc_run-* ${main}/func/
    cp -n ${new}/fmap/* ${main}/fmap/
    echo "copied localizer + fmap files into ${main}"
else
    echo "** localizer conversion incomplete - nothing copied; check err_dcm_loc"
fi
