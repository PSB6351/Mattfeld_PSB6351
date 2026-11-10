#!/bin/bash

#SBATCH -J psb6351_3dfwhmx
#SBATCH -o out_3dfwhmx
#SBATCH -e err_3dfwhmx
#SBATCH --qos classroom
#SBATCH --account acc_psb6351
#SBATCH --mem=32G

export PATH=$PATH:/home/applications/afni/25.2.07
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/motif-2.3.8-5gv6dfpysx6x42sq5ahtrb5xbvdvitdf/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libxt-1.3.1-io2ikvkn4dc5owt2whr5k7synmsmpyii/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libxft-2.3.8-dj2jatifobe67j534lbw3dnqqfn6olzg/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libxmu-1.2.1-2iyuzberhuplw6zkrfppayebxfwpde6x/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libsm-1.2.6-bfopuwkxowogrmgea22q3jog4m3icmbo/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libice-1.1.2-7dyepgav4bh335ib7miuy3uar2f5zoui/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libpng-1.6.47-hshbhaybhl3dg7pojxgaplot2djkwln2/lib64:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libxext-1.3.6-s2m6nnzuwvo2dvdjqby2lgmvgoebnebe/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libx11-1.8.11-dsqyqveqbcsztzcr5hou4vupdcnverqr/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libxpm-3.5.17-7tbkl7pprcdkknfzfd6zuvlpxeobuqif/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/mesa-25.0.5-ii4yqltj6qjf7iisbyyve5v4fgbqwcbg/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/mesa-glu-9.0.2-evnqwufx3z5anlf3sdb6uiormskw7qyz/lib:/home/applications/afni/25.2.07/lib

# Need to run the below line once:
#3dAutomask -prefix COMPLETE THIS LINE...WHAT ARE THE INPUTS, OUTPUTS,  INCLUDE AS A COMMENTED LINE WHY YOU ARE RUNNING THIS COMMAND

3dAutomask -prefix /home/eskog001/Mattfeld_PSB6351_eas/derivatives/preproc/sub-021/sub-021_mask.nii.gz /home/eskog001/Mattfeld_PSB6351_eas/derivatives/preproc/sub-021/filtered/_highpass0/sub-021_task-study_run-1_bold_volreg_tshift_maths_smooth_tempfilt.nii.gz

#3dFWHMx COMPLETE THIS LINE...WHAT INPUTS, OUTPUTS, FLAGS DO YOU NEED.  WHAT ARE YOU TRYING TO ACCOMPLISH WITH THIS LINE?

3dFWHMx -mask /home/eskog001/Mattfeld_PSB6351_eas/derivatives/preproc/sub-021/sub-021_mask.nii.gz -input /home/eskog001/Mattfeld_PSB6351_eas/derivatives/preproc/sub-021/filtered/_highpass0/sub-021_task-study_run-1_bold_volreg_tshift_maths_smooth_tempfilt.nii.gz -acf acf2

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

3dClustSim -mask /home/eskog001/Mattfeld_PSB6351_eas/derivatives/preproc/sub-021/sub-021_mask.nii.gz -acf 0.587693 2.73243 7.66919 -prefix psb6351_clustsim.1D
