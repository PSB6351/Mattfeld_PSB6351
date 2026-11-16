#!/bin/bash

#SBATCH -J psb6351_3dfwhmx
#SBATCH -o out_3dfwhmx
#SBATCH -e err_3dfwhmx
#SBATCH --qos classroom
#SBATCH --account acc_psb6351
#SBATCH --partition default-part
#SBATCH --mem=16G

data_dir=/home/mali092/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref

# Input: Preprocessed BOLD image from the first REVL study run.
input_file="/home/mali092/Mattfeld_PSB6351/derivatives/preproc/sub-021/func/_temporal_filter0/sub-021_task-REVL_run-1_bold_volreg_tshift_masked_smooth_tempfilt.nii.gz"

# Output: Brain mask generated from the input BOLD image.
mask_file="${data_dir}/sub-021_mask.nii.gz"

# Need to run the below line once:
3dAutomask \
    -prefix "$mask_file"\
    "$input_file"

# COMPLETE THIS LINE...WHAT ARE THE INPUTS, OUTPUTS,  INCLUDE AS A COMMENTED LINE WHY YOU ARE RUNNING THIS COMMAND
# INPUT  - preprocessed BOLD image from REVL run 1 
#OUTPUT - binary brain mask
# 3dAutomask creates a brain msk identifying brain voxels and excludes surrounding non brain regions to ensure that smoothness estimations are restricted to the brain rather than the whole image volume.

3dFWHMx \
    -input "$input_file" \
    -mask "$mask_file" \
    -detrend \
    -acf acf2 \
    > fwhmx_results.1D
    
#COMPLETE THIS LINE...WHAT INPUTS, OUTPUTS, FLAGS DO YOU NEED.  WHAT ARE YOU TRYING TO ACCOMPLISH WITH THIS LINE?
#INPUT  - Preprocessed BOLD data and the brain mask
#OUTPUT - fwhmx_results.1D containing smoothness estimates and acf2 containing the spatial autocorrelation function
#FLAGS  - 
# 3dFWHMx estimates the spatial smoothness of the fMRI noise, Nearby voxels are not statistically independent because of spatial moothing and intrinsic spatial correlations

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

#The four masked values are the three fitted ACF parameters
# (a, b, c), followed by the effective FWHM.
# a = relative contribution of the Gaussian component.
# b = Gaussian spatial scale in millimeters.
# c = exponential spatial decay scale in millimeters.
# Fourth value = effective FWHM in millimeters.

read -r a b c fwhm < <(tail -n 1 fwhmx_results.1D)

# Display the ACF parameters.
echo "ACF a = $a"
echo "ACF b = $b"
echo "ACF c = $c"
echo "Effective FWHM = $fwhm"

3dClustSim -mask "$mask_file" -acf "$a" "$b" "$c" -prefix psb6351_clustsim
