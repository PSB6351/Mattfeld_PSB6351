#!/bin/bash

#SBATCH -J psb6351_3dfwhmx
#SBATCH -o out_3dfwhmx
#SBATCH -e err_3dfwhmx
#SBATCH --qos pq_madlab
#SBATCH --account iacc_madlab
#SBATCH --partition 16C_128G
module load afni

# Need to run the below line once:
# Makes a brain mask from the functional image so smoothness is only estimated
# inside the brain, not the empty space around the head
3dAutomask -prefix /home/cknowlto/Mattfeld_PSB6351/derivatives/preproc_only_slice_and_motion_correction/sub-021/motion/sub-021_mask.nii.gz /home/cknowlto/Mattfeld_PSB6351/derivatives/preproc_only_slice_and_motion_correction/sub-021/motion/sub-021_task-study_run-3_bold_roi.nii.gz

3dFWHMx -mask /home/cknowlto/Mattfeld_PSB6351/derivatives/preproc_only_slice_and_motion_correction/sub-021/motion/sub-021_mask.nii.gz -input /home/cknowlto/Mattfeld_PSB6351/derivatives/preproc_only_slice_and_motion_correction/sub-021/motion/sub-021_task-study_run-3_bold_roi.nii.gz -acf acf2

# THE OUTPUT SHOULD LOOK SOMETHING LIKE THE TEXT BELOW:

#++ 3dFWHMx: AFNI version=AFNI_20.2.10 (Aug  4 2020) [64-bit]
#++ Authored by: The Bob
#*+ WARNING:   If you are performing spatial transformations on an oblique dset, 
#  such as /home/amattfel/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_mask.nii.gz,
#  or viewing/combining it with volumes of differing obliquity,
#  you should consider running: 
#     3dWarp -deoblique 
#  on this and  other oblique datasets in the same session.
# See 3dWarp -help for details.
#++ Oblique dataset:/home/amattfel/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_mask.nii.gz is 30.000002 degrees from plumb.
#++ Number of voxels in mask = 220228
#++ Oblique dataset:/home/amattfel/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_task-loc_run-1_bold_roi.nii.gz is 30.000002 degrees from plumb.
#++ start ACF calculations out to radius = 17.31 mm
# + ACF done (0.00 CPU s thus far)
# old-style FWHM parameters
# 0  0  0    0
# ACF model parameters for a*exp(-r*r/(2*b*b))+(1-a)*exp(-r/c) plus effective FWHM
#--># #######  #######  #######    ###### <-- THIS IS THE MOST IMPORTANT LINE....WHAT HAS BEEN MASKED HERE THAT YOU NEED FOR COMMAND BELOW?
#++ ACF 1D file [radius ACF mixed_model gaussian_NEWmodel] written to acf2
#++ 1dplot: AFNI version=AFNI_20.2.10 (Aug  4 2020) [64-bit]
#++ Authored by: RWC et al.
#++ and 1dplot-ed to file acf2.png

3dClustSim -mask /home/cknowlto/Mattfeld_PSB6351/derivatives/preproc_only_slice_and_motion_correction/sub-021/motion/sub-021_mask.nii.gz -acf A B C -prefix psb6351_clustsim.1D