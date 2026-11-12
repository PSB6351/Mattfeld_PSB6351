#!/bin/bash

#SBATCH -J psb6351_3dfwhmx
#SBATCH -o out_3dfwhmx
#SBATCH -e err_3dfwhmx
#SBATCH --qos classroom
#SBATCH --account acc_psb6351
#SBATCH --cpus-per-task 4
#SBATCH --mem-per-cpu 2G

# Need to run the below line once:
#3dAutomask -prefix COMPLETE THIS LINE...WHAT ARE THE INPUTS, OUTPUTS,  INCLUDE AS A COMMENTED LINE WHY YOU ARE RUNNING THIS COMMAND
T
# 3dAutomask creates a brain-only binary mask dataset (composed of 0 for outside the brain and 1 for inside the brain) based on EPI or skull-stripped anatomical data. Looking at a breakdown by Andy's Brain Book (https://andysbrainbook.readthedocs.io/en/stable/AFNI/AFNI_Short_Course/AFNI_Preprocessing/06_AFNI_Masking_Scaling.html), 
# our data can be reduced by applying a mask, which would indicate which voxels should be analyzed in AFNI. This binary separation is like tracing an outline on paper before cutting out your desired image! Here,
# assumed noise is cut off via the 3dAutomask line. 

# Basically, this line will build a mask based on our reference image (AKA, input = the
# study_ref bold_roi image, output = sub-021_mask.nii.gz), restricting 3dFWHMx to
# our desired brain voxels!

#3dAutomask -prefix /home/amele052/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_mask.nii.gz /home/amele052/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_task-REVL_run-01_bold_roi.nii.gz
# Here, the 3dAutomask line makes a brain mask from the study_ref functional image; output path is for the mask file that 3dAutomask creates.

# ----------------------------------------------------------------- 

#3dFWHMx COMPLETE THIS LINE...WHAT INPUTS, OUTPUTS, FLAGS DO YOU NEED.  WHAT ARE YOU TRYING TO ACCOMPLISH WITH THIS LINE?

# The goal for this 3dFWHMx line is to estimate the amount of smoothness (RECALL!! INTRINSIC SPATIAL SMOOTHNESS) of the noise in our data. 
# By gathering/estimating smoothness, this can then be applied to the 3dClustStim line below to run Montecarlo simulations! 
# -mask directs 3dFWHMx to only use voxels inside the brain mask created above! If no mask was made, then this line would estimate smoothness in the entire image, including empty space and noise around the head, which we do not want! 
# adding -acf acf2 tells 3dFWHMx to model the data’s smoothness with the autocorrelation function (ACF) and save the results under the name acf2.
# ACF creates four numbered outputs, or parameters, fitting the mixed-Gaussian (i.e., Gaussian + exponential, hence these two lines) model discussed in class! Three parameters and our effective FWHM.

# as for -input, that names the data file, AKA the bold_roi image; the flag mark distinguishes which path is the data and which is the mask. 

# ----------------------------------------------------------------- 

# clues to what should go where can be picked out in this example output! 

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

# ^^ The masked values above represent the ACF parameters a, b, c (4th number = FWHM).
# The first three numbers (a b c) go after -acf in 3dClustSim!


#++ ACF 1D file [radius ACF mixed_model gaussian_NEWmodel] written to acf2
#++ 1dplot: AFNI version=AFNI_20.2.10 (Aug  4 2020) [64-bit]
#++ Authored by: RWC et al.
#++ and 1dplot-ed to file acf2.png

# ----------------------------------------------------------------- 

# Once the two lines above run, 3dAutomask should create the brain mask, and 3dFWHMx should provide the four parameter values you need for our ACF line.
# From what my terminal output gave me, those values are: 0.480572  24.9153  4.75515    20.6754
# The first three will go into the 3dClustStim below! The fourth #, 20.6754 is the effective FWHM in mm. Also, 3dAutomask made a mask using 220494 voxels (output message said: Mask now has 220494 voxels).

# Now that the two lines ran once, I will comment them out so they remain in the script, but they won't run again.  

#3dClustSim -mask WHAT GOES HERE??? -acf ######  ######  ####### -prefix psb6351_clustsim.1D
3dClustSim -mask /home/amele052/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_mask.nii.gz -acf 0.480572 24.9153 4.75515 -prefix psb6351_clustsim.1D

# While running 3dClustSim, I realized it was running...for an INSANELY long time. To see if this helps with the speed of running this line, I added two #SBATCH lines at the top, taking reference to an earlier assignment! 
# Specifically, I wenapt based off an edit I made to my preproc workflow from an earlier assignment, and I specified the amount of cpus-per-task that I wanted, as well as 
# the amount of memory-per-cpu. Note that requesting more memory may go beyond what the --qos allows and may result in a longer queue time! 