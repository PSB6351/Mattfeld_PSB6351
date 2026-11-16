#!/bin/bash

#SBATCH -J psb6351_3dfwhmx
#SBATCH -o out_3dfwhmx
#SBATCH -e err_3dfwhmx
#SBATCH --qos highmem1
#SBATCH --account acc_madlab
#SBATCH --partition highmem1-sapphirerapids

# ======================
# Paths & Variables
# ======================
# Setting paths&vars so that the commands are easier to run
SUB=sub-021
FWHM=3.0 #Which smoothing level to use, needs to match 1 of the fwhm-X folders
# Since I did 4 kernels, I could make my choice. I decided on 3.0 because I think it will relate better to my future questions for the final paper, preserving the data by smoothing less.
PREPROC_DIR=/home/sfrai003/Mattfeld_PSB6351/derivatives/preproc/${SUB}
OUT_DIR=/home/sfrai003/Mattfeld_PSB6351/derivatives/clustsim/${SUB}
# created a new folder for this output^
ERRTS_DIR=${PREPROC_DIR}/tempfilt_afni_susan/fwhm-${FWHM}
REF=${PREPROC_DIR}/study_ref/${SUB}_ses-S1_task-ROI_loc_run-1_roi.nii.gz

mkdir -p ${OUT_DIR}
cd ${OUT_DIR} # this will put the outputs in the outdir!
# except for the err and out files, which are in the code dir

# -------- STEP 1: BRAIN MASK (RUN 1x) --------
# A.M. Notes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Need to run the below line once:
#3dAutomask -prefix COMPLETE THIS LINE...WHAT ARE THE INPUTS, OUTPUTS,  INCLUDE AS A COMMENTED LINE WHY YOU ARE RUNNING THIS COMMAND
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Format to help me:
# 3dAutomask -prefix <output mask> <input dataset>
# Input: Study reference functional volume??
# Output: Binarized brain only mask.
# Why?: So 3dFWHMx and 3dClustSim only use voxels inside the brain. Air and skull are noise and distort smoothness, signal, etc.

# commenting out because I ran successfully
#3dAutomask -prefix ${SUB}_mask.nii.gz ${REF}


# ------- STEP 2: Estimate Smoothness (ACF) for each run -------
# I am confused on if I am doing this for all runs^?? Feels like i am doing something wrong.

# A.M. Notes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`
#3dFWHMx COMPLETE THIS LINE...WHAT INPUTS, OUTPUTS, FLAGS DO YOU NEED.  WHAT ARE YOU TRYING TO ACCOMPLISH WITH THIS LINE?

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
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Notes to help me:
# 3dFWHMx -mask <mask> -input <errts> -acf <name>
# Input: I am using the residual (err) time series from the model fit (1 per run)
# I think i do not need -detrend because the error time series is already detrended (based on information from the link/afni help)
# ** Confusion: online link says the input can be either raw data going into 3ddeconvolve or error data coming out of 3ddeconvolve. What would be the reason for choosing either approach? Pros/cons?
# Goal: Measuring how spatially smooth it is using ACF model
# ---> is "IT" the noise because I chose the error files? does that mean i made the wrong choice, or just a different one?
# -------> from what i can grasp, using the errts works bc it means you are estimating the spatial smoothness and autocorrelation of the noise, not task-evoked signals... which is good for the 3dclustsim part. i think its starting to make sense, was just doubting the process.
# ACF = spatial autocorrelation function, how strongly neighboring voxels noise is correlated?? (distance) 

# commenting out bc i ran it successfully (i think)
#3dFWHMx -mask ${SUB}_mask.nii.gz -input ${ERRTS_DIR}/_remlfit0/detrended_errts.nii.gz -ACF acf1
# --> output numbers were: 0.636929  1.74279  6.43077  4.83746

#***Confusion: This is only using 1 run for simplicity, or were we supposed to do all of them? Wouldn't this (positively) affect the ACF?

# ------- STEP 3: Cluster-Size Thresholds -------
# 3dclustSim: estiamtes probability of false positive clusters (so noise-only.
# simulate noise volume given ACF parameters (3)
# determining cluster size thresholds for fmri data, false positve rate control

3dClustSim -mask ${SUB}_mask.nii.gz -acf 0.636929 1.74279 6.43077 -prefix psb6351_clustsim.1D
