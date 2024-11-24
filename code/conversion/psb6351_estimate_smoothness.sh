#!/bin/bash

#SBATCH -J psb6351_3dfwhmx
#SBATCH -o out_3dfwhmx
#SBATCH -e err_3dfwhmx
#SBATCH --qos pq_madlab
#SBATCH --account iacc_madlab
#SBATCH --partition 16C_128G

# Need to run the below line once:
# Creating mask using automask
3dAutomask -prefix ~/Mattfeld_PSB6351/derivatives/preproc_motion_first/sub-021/study_ref/sub-021_mask.nii.gz ~/Mattfeld_PSB6351/derivatives/preproc_motion_first/sub-021/study_ref/sub-021_task-loc_run-1_bold_roi.nii.gz

# Creating mask
3dFWHMx -acf -out loc_3dfwhmx_output -mask ~/Mattfeld_PSB6351/derivatives/preproc_motion_first/sub-021/study_ref/sub-021_mask.nii.gz -input ~/Mattfeld_PSB6351/derivatives/preproc_motion_first/sub-021/study_ref/sub-021_task-loc_run-1_bold_roi.nii.gz

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
# old-style FWHM parameters3dFWHMx -acf -out loc_3dfwhmx_output -mask ~/Mattfeld_PSB6351/derivatives/preproc_motion_first/sub-021/study_ref/sub-021_custom_mask.nii.gz -input ~/Mattfeld_PSB6351/derivatives/preproc_motion_first/sub-021/study_ref/sub-021_task-loc_run-1_bold_roi.nii.gz

# 0  0  0    0
# ACF model parameters for a*exp(-r*r/(2*b*b))+(1-a)*exp(-r/c) plus effective FWHM
#--># 0.488832  24.7677  4.73696    21.264 <--
#++ ACF 1D file [radius ACF mixed_model gaussian_NEWmodel] written to acf2
#++ 1dplot: AFNI version=AFNI_20.2.10 (Aug  4 2020) [64-bit]
#++ Authored by: RWC et al.
#++ and 1dplot-ed to file acf2.png

#playing with double
3dClustSim -mask ~/Mattfeld_PSB6351/derivatives/preproc_motion_first/sub-021/study_ref/sub-021_mask.nii.gz -acf 0.488832  24.7677  4.73696 -prefix psb6351_clustsim_x1.1D
3dClustSim -mask ~/Mattfeld_PSB6351/derivatives/preproc_motion_first/sub-021/study_ref/sub-021_mask.nii.gz -acf 0.488832  24.7677  9.47392 -prefix psb6351_clustsim_x2.1D
3dClustSim -mask ~/Mattfeld_PSB6351/derivatives/preproc_motion_first/sub-021/study_ref/sub-021_mask.nii.gz -acf 0.488832 24.7677 14.21088 -prefix psb6351_clustsim_x3.1D

#Values from 3dFWHMx
3dClustSim -mask ~/Mattfeld_PSB6351/derivatives/preproc_motion_first/sub-021/study_ref/sub-021_mask.nii.gz -acf 0.484028 25.7138 4.70501 -prefix psb6351_clustsim.1D


#!/bin/bash

#SBATCH -J psb6351_3dfwhmx
#SBATCH -o out_3dfwhmx
#SBATCH -e err_3dfwhmx
#SBATCH --qos pq_madlab
#SBATCH --account iacc_madlab
#SBATCH --partition 16C_128G

# Need to run the below line once:
#3dAutomask -prefix ~/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_mask.nii.gz ~/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_task-loc_run-1_bold_roi.nii.gz

#3dFWHMx -acf -out loc_3dfwhmx_output -mask ~/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_mask.nii.gz -input ~/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_task-loc_run-1_bold_roi.nii.gz

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
#--># 0.488832  24.7677  4.73696    21.264 <--
#++ ACF 1D file [radius ACF mixed_model gaussian_NEWmodel] written to acf2
#++ 1dplot: AFNI version=AFNI_20.2.10 (Aug  4 2020) [64-bit]
#++ Authored by: RWC et al.
#++ and 1dplot-ed to file acf2.png

3dClustSim -mask ~/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_mask.nii.gz -acf 0.488832  24.7677  4.73696 -prefix psb6351_clustsim.1D
