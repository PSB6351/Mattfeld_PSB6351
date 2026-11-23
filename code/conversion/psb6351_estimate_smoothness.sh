#!/bin/bash

#SBATCH -J psb6351_3dfwhmx
#SBATCH -o out_3dfwhmx
#SBATCH -e err_3dfwhmx
#SBATCH --qos=classroom
#SBATCH --account=acc_psb6351
#SBATCH --partition=default-part
#SBATCH --mem=8G


# Need to run the below line once:
#3dAutomask -prefix COMPLETE THIS LINE...WHAT ARE THE INPUTS, OUTPUTS,  INCLUDE AS A COMMENTED LINE WHY YOU ARE RUNNING THIS COMMAND

# 3dAutomask uses the functional reference image as input to generate a binary brain mask as output, which excludes nonbrain voxels so that smoothness estimation and cluster simulation are restricted to brain tissue.

#3dAutomask -prefix ../../derivatives/preproc/sub-021/study_ref/sub-021_mask.nii.gz ../../derivatives/preproc/sub-021/study_ref/sub-021_task-REVL_run-01_bold_roi.nii.gz


#3dFWHMx COMPLETE THIS LINE...WHAT INPUTS, OUTPUTS, FLAGS DO YOU NEED.  WHAT ARE YOU TRYING TO ACCOMPLISH WITH THIS LINE?

# 3dFWHMx uses the functional image and brain mask as inputs to estimate spatial smoothness within the brain. The -mask flag restricts the analysis to brain voxels, while -acf estimates the spatial autocorrelation parameters needed for cluster-size correction and saves the results to acf2.

3dFWHMx -detrend -mask ../../derivatives/preproc/sub-021/study_ref/sub-021_mask.nii.gz -acf acf2 -input ../../derivatives/preproc/sub-021/smoothed/_fwhm_6/_smooth0/sub-021_task-REVL_run-01_bold_volreg_tshift_smooth.nii.gz


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

3dClustSim -mask ../../derivatives/preproc/sub-021/study_ref/sub-021_mask.nii.gz -acf 0.686777 3.93611 12.4821 -prefix psb6351_clustsim.1D
