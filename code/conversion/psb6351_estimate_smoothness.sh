#!/bin/bash

#SBATCH -J psb6351_3dfwhmx
#SBATCH -o out_3dfwhmx
#SBATCH -e err_3dfwhmx
#SBATCH --qos pq_madlab
#SBATCH --account iacc_madlab
#SBATCH --partition 16C_128G

ref_dir=/home/cbeac004/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref

# Need to run the below line once:
# Input: the EPI reference volume (study_ref). Output: a binary brain mask (sub-021_mask.nii.gz).
# Why: 3dFWHMx and 3dClustSim should only use brain voxels. Outside-brain voxels are just noise
# and would make the smoothness estimate and the simulated search volume wrong.
3dAutomask -prefix ${ref_dir}/sub-021_mask.nii.gz ${ref_dir}/sub-021_task-REVL_run-01_bold_roi.nii.gz

# Estimate the spatial smoothness of the data inside the brain mask.
# -mask: only use brain voxels. -acf: fit the spatial autocorrelation function
# (a*exp(-r*r/(2*b*b))+(1-a)*exp(-r/c)) instead of assuming a pure Gaussian, and write it to acf2 / acf2.png.
# The last line printed is "a b c effective_FWHM"; a, b, c are what 3dClustSim needs.
acf=$(3dFWHMx -mask ${ref_dir}/sub-021_mask.nii.gz -acf acf2 -input ${ref_dir}/sub-021_task-REVL_run-01_bold_roi.nii.gz | tail -n 1)
echo "ACF a b c FWHM: ${acf}"
set -- ${acf}

# MOST IMPORTANT LINE: "a b c FWHM". What was masked: the non-brain voxels (brain mask).
# 3dClustSim needs that same mask plus the first three numbers (a b c). The 4th is the effective FWHM in mm.

# Simulate noise-only data with the same smoothness (ACF a b c) inside the same brain mask to find
# the minimum cluster size needed at each voxel p-threshold for a given corrected alpha.
3dClustSim -mask ${ref_dir}/sub-021_mask.nii.gz -acf $1 $2 $3 -iter 1000 -prefix psb6351_clustsim
