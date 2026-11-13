#!/bin/bash

#SBATCH -J psb6351_3dfwhmx
#SBATCH -o out_3dfwhmx
#SBATCH -e err_3dfwhmx
#SBATCH --qos pq_madlab
#SBATCH --account iacc_madlab
#SBATCH --partition 16C_128G

# ---- paths ----
sub=sub-021
ref_dir=/home/aoste011/Mattfeld_PSB6351/derivatives/preproc/${sub}/study_ref
bold=${ref_dir}/${sub}_task-loc_run-01_bold_roi.nii.gz
out_dir=/home/aoste011/Mattfeld_PSB6351/code/conversion/smoothness_outputs
mask=${out_dir}/${sub}_mask.nii.gz

mkdir -p ${out_dir}
cd ${out_dir}

# Need to run the below line once (already run):
# Make a brain mask from the functional data so smoothness is only estimated
# inside the brain (not the air/noise around the head)
#3dAutomask -prefix ${mask} ${bold}

# Estimate the spatial smoothness of the data inside the brain mask using the ACF model (already run).
# Output: a=0.506649 b=24.4878 c=4.53657, effective FWHM=22.1896 mm
#3dFWHMx -mask ${mask} -input ${bold} -acf acf2 > fwhmx_results.txt

# Simulate noise with the measured smoothness (ACF a, b, c) inside the same mask to find
# the minimum cluster size needed at each voxel p-threshold and corrected alpha (replaces AlphaSim)
3dClustSim -mask ${mask} -acf 0.506649 24.4878 4.53657 -prefix psb6351_clustsim
