#!/bin/bash

#SBATCH -J psb6351_3dfwhmx
#SBATCH -o out_3dfwhmx
#SBATCH -e err_3dfwhmx
#SBATCH --qos pq_madlab
#SBATCH --account iacc_madlab
#SBATCH --partition 16C_128G

#3dAutomask -prefix /home/crees016/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_mask.nii.gz /home/crees016/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_task-loc_run-1_bold_roi.nii.gz

# commented all others, and uncommented 3dAutomask and inputted this into the terminal:
# ./psb6351_estimate_smoothness.sh

# CHRIS'S 3dAutomask terminal printout:
'''
++ 3dAutomask: AFNI version=AFNI_20.2.10 (Aug  4 2020) [64-bit]
++ Authored by: Emperor Zhark
*+ WARNING:   If you are performing spatial transformations on an oblique dset, 
  such as /home/crees016/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_task-loc_run-1_bold_roi.nii.gz,
  or viewing/combining it with volumes of differing obliquity,
  you should consider running: 
     3dWarp -deoblique 
  on this and  other oblique datasets in the same session.
 See 3dWarp -help for details.
++ Oblique dataset:/home/crees016/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_task-loc_run-1_bold_roi.nii.gz is 30.000002 degrees from plumb.
++ Loading dataset /home/crees016/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_task-loc_run-1_bold_roi.nii.gz
++ Forming automask
 + Fixed clip level = 126.472397
 + Used gradual clip level = 93.551201 .. 153.040497
 + Number voxels above clip level = 235097
 + Clustering voxels ...
 + Largest cluster has 230141 voxels
 + Clustering voxels ...
 + Largest cluster has 210825 voxels
 + Filled  3643 voxels in small holes; now have 214468 voxels
 + Filled  5652 voxels in large holes; now have 220120 voxels
 + Clustering voxels ...
 + Largest cluster has 220113 voxels
 + Clustering non-brain voxels ...
 + Clustering voxels ...
 + Largest cluster has 439772 voxels
 + Mask now has 220228 voxels
++ 220228 voxels in the mask [out of 660000: 33.37%]
++ first  12 x-planes are zero [from R]
++ last   14 x-planes are zero [from L]
++ first   0 y-planes are zero [from P]
++ last    2 y-planes are zero [from A]
++ first   0 z-planes are zero [from I]
++ last    0 z-planes are zero [from S]
++ Output dataset /home/crees016/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_mask.nii.gz
++ CPU time = 0.000000 sec
'''

#3dFWHMx -acf -out loc_3dfwhmx_output -mask /home/crees016/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_mask.nii.gz -input /home/crees016/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_task-loc_run-1_bold_roi.nii.gz

# recommented others and uncommented 3dFWHMx and inputted this into the terminal:
# ./psb6351_estimate_smoothness.sh

# CHRIS'S 3dFWHMx terminal printout:
'''
++ 3dFWHMx: AFNI version=AFNI_20.2.10 (Aug  4 2020) [64-bit]
++ Authored by: The Bob
*+ WARNING:   If you are performing spatial transformations on an oblique dset, 
  such as /home/crees016/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_mask.nii.gz,
  or viewing/combining it with volumes of differing obliquity,
  you should consider running: 
     3dWarp -deoblique 
  on this and  other oblique datasets in the same session.
 See 3dWarp -help for details.
++ Oblique dataset:/home/crees016/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_mask.nii.gz is 30.000002 degrees from plumb.
++ Number of voxels in mask = 220228
++ Oblique dataset:/home/crees016/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_task-loc_run-1_bold_roi.nii.gz is 30.000002 degrees from plumb.
++ start ACF calculations out to radius = 17.31 mm
 + ACF done (0.00 CPU s thus far)
 0  0  0    0
 0.488851  24.7656  4.73671    21.2642
++ ACF 1D file [radius ACF mixed_model gaussian_NEWmodel] written to 3dFWHMx.1D
++ 1dplot: AFNI version=AFNI_20.2.10 (Aug  4 2020) [64-bit]
++ Authored by: RWC et al.
 + and 1dplot-ed to file 3dFWHMx.1D.png
'''

# adjusted parameters for 3dClustSum based on above printout
# 0.488851  24.7656  4.73671    21.2642

# commented others, and uncommented 3dClustSim with new parameters
# 3dClustSim -mask /home/crees016/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_mask.nii.gz -acf 0.488851  24.7656  4.73671 -prefix psb6351_clustsim.1D

# CHRIS'S 3dClustSim terminal printout:
'''
./psb6351_estimate_smoothness.sh: line 53: 
++ 3dAutomask: AFNI version=AFNI_20.2.10 (Aug  4 2020) [64-bit]
++ Authored by: Emperor Zhark
*+ WARNING:   If you are performing spatial transformations on an oblique dset, 
  such as /home/crees016/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_task-loc_run-1_bold_roi.nii.gz,
  or viewing/combining it with volumes of differing obliquity,
  you should consider running: 
     3dWarp -deoblique 
  on this and  other oblique datasets in the same session.
 See 3dWarp -help for details.
++ Oblique dataset:/home/crees016/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_task-loc_run-1_bold_roi.nii.gz is 30.000002 degrees from plumb.
++ Loading dataset /home/crees016/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_task-loc_run-1_bold_roi.nii.gz
++ Forming automask
 + Fixed clip level = 126.472397
 + Used gradual clip level = 93.551201 .. 153.040497
 + Number voxels above clip level = 235097
 + Clustering voxels ...
 + Largest cluster has 230141 voxels
 + Clustering voxels ...
 + Largest cluster has 210825 voxels
 + Filled  3643 voxels in small holes; now have 214468 voxels
 + Filled  5652 voxels in large holes; now have 220120 voxels
 + Clustering voxels ...
 + Largest cluster has 220113 voxels
 + Clustering non-brain voxels ...
 + Clustering voxels ...
 + Largest cluster has 439772 voxels
 + Mask now has 220228 voxels
++ 220228 voxels in the mask [out of 660000: 33.37%]
++ first  12 x-planes are zero [from R]
++ last   14 x-planes are zero [from L]
++ first   0 y-planes are zero [from P]
++ last    2 y-planes are zero [from A]
++ first   0 z-planes are zero [from I]
++ last    0 z-planes are zero [from S]
++ Output dataset /home/crees016/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_mask.nii.gz
++ CPU time = 0.000000 sec
: No such file or directory
./psb6351_estimate_smoothness.sh: line 82: 
++ 3dFWHMx: AFNI version=AFNI_20.2.10 (Aug  4 2020) [64-bit]
++ Authored by: The Bob
*+ WARNING:   If you are performing spatial transformations on an oblique dset, 
  such as /home/crees016/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_mask.nii.gz,
  or viewing/combining it with volumes of differing obliquity,
  you should consider running: 
     3dWarp -deoblique 
  on this and  other oblique datasets in the same session.
 See 3dWarp -help for details.
++ Oblique dataset:/home/crees016/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_mask.nii.gz is 30.000002 degrees from plumb.
++ Number of voxels in mask = 220228
++ Oblique dataset:/home/crees016/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_task-loc_run-1_bold_roi.nii.gz is 30.000002 degrees from plumb.
++ start ACF calculations out to radius = 17.31 mm
 + ACF done (0.00 CPU s thus far)
 0  0  0    0
 0.488851  24.7656  4.73671    21.2642
++ ACF 1D file [radius ACF mixed_model gaussian_NEWmodel] written to 3dFWHMx.1D
++ 1dplot: AFNI version=AFNI_20.2.10 (Aug  4 2020) [64-bit]
++ Authored by: RWC et al.
 + and 1dplot-ed to file 3dFWHMx.1D.png
: No such file or directory
++ 3dClustSim: AFNI version=AFNI_20.2.10 (Aug  4 2020) [64-bit]
++ Authored by: RW Cox and BD Ward
*+ WARNING:   If you are performing spatial transformations on an oblique dset, 
  such as /home/crees016/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_mask.nii.gz,
  or viewing/combining it with volumes of differing obliquity,
  you should consider running: 
     3dWarp -deoblique 
  on this and  other oblique datasets in the same session.
 See 3dWarp -help for details.
++ Oblique dataset:/home/crees016/Mattfeld_PSB6351/derivatives/preproc/sub-021/study_ref/sub-021_mask.nii.gz is 30.000002 degrees from plumb.
++ 220228 voxels in mask (33.37% of total)
++ Kernel function radius = 62.62 mm
++ ACF(0.49,24.77,4.74) => FWHM=21.26 => 100x100x66 pads to 192x192x160
 + Kernel image dimensions 95 x 95 x 79
++ Startup clock time = 0.8 s
++ Using 4 OpenMP threads
Simulating:0123456789.0123456789.0123456789.0123456789.0123456789.!
++ Clock time now = 1053.3 s
'''

