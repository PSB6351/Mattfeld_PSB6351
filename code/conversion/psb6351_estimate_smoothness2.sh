#!/bin/bash

#SBATCH -J psb6351_3dfwhmx
#SBATCH -o out_3dfwhmx
#SBATCH -e err_3dfwhmx
#SBATCH --qos classroom
#SBATCH --account acc_psb6351
#SBATCH --mem=32G

export PATH=$PATH:/home/applications/afni/25.2.07
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/motif-2.3.8-5gv6dfpysx6x42sq5ahtrb5xbvdvitdf/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libxt-1.3.1-io2ikvkn4dc5owt2whr5k7synmsmpyii/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libxft-2.3.8-dj2jatifobe67j534lbw3dnqqfn6olzg/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libxmu-1.2.1-2iyuzberhuplw6zkrfppayebxfwpde6x/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libsm-1.2.6-bfopuwkxowogrmgea22q3jog4m3icmbo/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libice-1.1.2-7dyepgav4bh335ib7miuy3uar2f5zoui/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libpng-1.6.47-hshbhaybhl3dg7pojxgaplot2djkwln2/lib64:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libxext-1.3.6-s2m6nnzuwvo2dvdjqby2lgmvgoebnebe/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libx11-1.8.11-dsqyqveqbcsztzcr5hou4vupdcnverqr/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libxpm-3.5.17-7tbkl7pprcdkknfzfd6zuvlpxeobuqif/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/mesa-25.0.5-ii4yqltj6qjf7iisbyyve5v4fgbqwcbg/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/mesa-glu-9.0.2-evnqwufx3z5anlf3sdb6uiormskw7qyz/lib:/home/applications/afni/25.2.07/lib

preproc_dir=/home/eskog001/Mattfeld_PSB6351_eas/derivatives/preproc/sub-021
mask_file=${preproc_dir}/sub-021_mask.nii.gz

# Need to run the below line once:
#3dAutomask -prefix COMPLETE THIS LINE...WHAT ARE THE INPUTS, OUTPUTS,  INCLUDE AS A COMMENTED LINE WHY YOU ARE RUNNING THIS COMMAND
# ALREADY RAN -mask exists. AFNI won't overwrite it, so leave commented out on reruns
# (same mask is reused for every kernel below so the search volume stays constant across comparisons)

#3dAutomask -prefix ${mask_file} ${preproc_dir}/filtered/_highpass0/sub-021_task-study_run-1_bold_volreg_tshift_maths_smooth_tempfilt.nii.gz

#3dFWHMx COMPLETE THIS LINE...WHAT INPUTS, OUTPUTS, FLAGS DO YOU NEED.  WHAT ARE YOU TRYING TO ACCOMPLISH WITH THIS LINE?

#-----------------------------------------------------------------------------------------------------------------------
# ORIGINAL 5mm KERNEL (already ran - ACF params below were taken from its output)
#3dFWHMx -mask ${mask_file} -input ${preproc_dir}/filtered/_highpass0/sub-021_task-study_run-1_bold_volreg_tshift_maths_smooth_tempfilt.nii.gz -acf acf2
#3dClustSim -mask ${mask_file} -acf 0.587693 2.73243 7.66919 -prefix psb6351_clustsim.1D

# EXTRA KERNELS (3mm, 6mm, 9mm, 12mm)

# for each kernel: estimate smoothness w/ 3dFWHMx, grab the a b c ACF params, pass them to 3dClustSim
# the last line 3dFWHMx prints to stdout is the ACF line: a  b  c  effective_FWHM
for fwhm in 3 6 9 12; do
    curr_file=${preproc_dir}/filtered_${fwhm}mm/_highpass_${fwhm}mm0/sub-021_task-study_run-1_bold_volreg_tshift_maths_smooth_tempfilt.nii.gz

    acf_params=$(3dFWHMx -mask ${mask_file} -input ${curr_file} -acf acf2_${fwhm}mm | tail -n 1)
    echo "${fwhm}mm ACF params (a b c FWHM): ${acf_params}" #this was tough to do. i first did this manually by scanning through the output, looked online for a better pipeline
    read acf_a acf_b acf_c acf_fwhm <<< "${acf_params}"

    3dClustSim -mask ${mask_file} -acf ${acf_a} ${acf_b} ${acf_c} -prefix psb6351_clustsim_${fwhm}mm.1D
done
