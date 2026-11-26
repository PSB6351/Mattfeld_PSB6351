#!/bin/bash
# Rebuilds the localizer and study-task design matrices.
# Same models as psb6351_evs.ipynb, PLUS one regressor per rapidart outlier volume.

base=/home/aoste011/Mattfeld_PSB6351
evs=$base/derivatives/first_lvl/sub-021/evs
mot=$base/derivatives/preproc/sub-021/motion
glm=$base/derivatives/glm/sub-021

# Save the matrices and pictures in the same place as before (code/conversion)
cd $base/code/conversion
rm -f X.loc.* X.task.*

# Add the outlier regressors only if rapidart flagged any volumes
loc_art=""
if [ -f $glm/sub-021_task-loc_outlier_regressors.1D ]; then
    loc_art="-ortvec $glm/sub-021_task-loc_outlier_regressors.1D art_outliers"
fi
study_art=""
if [ -f $glm/sub-021_task-study_outlier_regressors.1D ]; then
    study_art="-ortvec $glm/sub-021_task-study_outlier_regressors.1D art_outliers"
fi

# LOCALIZER: 2 runs x 304 volumes, TR = 1.76 s
3dDeconvolve -nodata 608 1.76 \
-concat '1D: 0 304' \
-ortvec $mot/allruns_loc_mot_data.1D motion \
$loc_art \
-polort A \
-local_times \
-num_stimts 2 \
-stim_times_AM1 1 $evs/loc_face_evs.1D "dmBLOCK(1)" -stim_label 1 faces \
-stim_times_AM1 2 $evs/loc_scene_evs.1D "dmBLOCK(1)" -stim_label 2 scenes \
-x1D X.loc.xmat.1D -xjpeg X.loc.jpg

# STUDY TASK: 4 runs x 355 volumes, TR = 1.76 s
3dDeconvolve -nodata 1420 1.76 \
-concat '1D: 0 355 710 1065' \
-ortvec $mot/allruns_task_mot_data.1D motion \
$study_art \
-polort A \
-local_times \
-num_stimts 5 \
-stim_times 1 $evs/fix_b4_c_cond_evs.1D "TWOGAMpw(4,5,0.2,12,7)" -stim_label 1 fx_b4_c_cond \
-stim_times 2 $evs/fix_b4_ic_cond_evs.1D "TWOGAMpw(4,5,0.2,12,7)" -stim_label 2 fx_b4_ic_cond \
-stim_times 3 $evs/events_remain_evs.1D "TWOGAMpw(4,5,0.2,12,7)" -stim_label 3 all_remain \
-stim_times 4 $evs/facefix_b4_bl_evs.1D "TWOGAMpw(4,5,0.2,12,7)" -stim_label 4 facefx_b4_bl \
-stim_times 5 $evs/scenefix_b4_bl_evs.1D "TWOGAMpw(4,5,0.2,12,7)" -stim_label 5 scenefx_b4_bl \
-x1D X.task.xmat.1D -xjpeg X.task.jpg
