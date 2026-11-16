#!/bin/bash

#SBATCH -J psb6351_3dfwhmx
#SBATCH -o out_3dfwhmx
#SBATCH -e err_3dfwhmx
#SBATCH --qos classroom
#SBATCH --account acc_psb6351
#SBATCH --mem=32G
# NOTE: class account/qos instead of the template's madlab ones (pq_madlab / iacc_madlab / 16C_128G)


# NOTE: AFNI paths for this cluster
export PATH=$PATH:/home/applications/afni/25.2.07
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/motif-2.3.8-5gv6dfpysx6x42sq5ahtrb5xbvdvitdf/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libxt-1.3.1-io2ikvkn4dc5owt2whr5k7synmsmpyii/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libxft-2.3.8-dj2jatifobe67j534lbw3dnqqfn6olzg/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libxmu-1.2.1-2iyuzberhuplw6zkrfppayebxfwpde6x/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libsm-1.2.6-bfopuwkxowogrmgea22q3jog4m3icmbo/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libice-1.1.2-7dyepgav4bh335ib7miuy3uar2f5zoui/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libpng-1.6.47-hshbhaybhl3dg7pojxgaplot2djkwln2/lib64:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libxext-1.3.6-s2m6nnzuwvo2dvdjqby2lgmvgoebnebe/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libx11-1.8.11-dsqyqveqbcsztzcr5hou4vupdcnverqr/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libxpm-3.5.17-7tbkl7pprcdkknfzfd6zuvlpxeobuqif/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/mesa-25.0.5-ii4yqltj6qjf7iisbyyve5v4fgbqwcbg/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/mesa-glu-9.0.2-evnqwufx3z5anlf3sdb6uiormskw7qyz/lib:/home/applications/afni/25.2.07/lib

preproc_dir=/home/eskog001/Mattfeld_PSB6351_eas/derivatives/preproc/sub-021
mask_file=${preproc_dir}/sub-021_mask.nii.gz
func_name=sub-021_task-study_run-1_bold_volreg_tshift_maths_smooth_tempfilt.nii.gz

# smoothing kernels (mm) to evaluate - all made by preproc5.py (5mm = original SUSAN node that i used in preproc1 & 2)
fwhms="3 5 6 9 12"

# summary table of every kernel's results (written at the end of each loop)
summary_file=smoothness_summary.txt
echo -e "kernel_mm\ta\tb\tc\teffective_FWHM_mm\tk_NN1_2sided_p001_a05" > ${summary_file}

#-----------------------------------------------------------------------------------------------------------------------
# Need to run the below line once:
#3dAutomask -prefix COMPLETE THIS LINE...WHAT ARE THE INPUTS, OUTPUTS,  INCLUDE AS A COMMENTED LINE WHY YOU ARE RUNNING THIS COMMAND
# WHY: 3dAutomask builds a brain-only mask from the preprocessed EPI. Smoothness should be
# estimated (3dFWHMx) and noise clusters simulated (3dClustSim) only INSIDE the brain - the empty
# space around the head would distort the smoothness estimate, and the mask sets the size + shape
# of the search volume that 3dClustSim simulates over.
# INPUT:  the 5mm smoothed + filtered study run-1 time series
# OUTPUT: sub-021_mask.nii.gz -> 203370 voxels (30.81% of volume); instructor example = 220228
# NOTE: only runs if the mask doesn't exist yet (AFNI won't overwrite it). the SAME mask is used for
# every kernel so the search volume is identical across kernels
if [ ! -f ${mask_file} ]; then
    3dAutomask -prefix ${mask_file} ${preproc_dir}/filtered/_highpass0/${func_name}
fi # just learnt how to close out if statements in bash; it's pretty funny

#-----------------------------------------------------------------------------------------------------------------------
for fwhm in ${fwhms}; do
    # 5mm keeps the original datasink folder + template output names (acf2, psb6351_clustsim.1D)
    # the extra kernels get their own folders (preproc3.py NODE 13) + a _<fwhm>mm suffix
    if [ ${fwhm} -eq 5 ]; then
        func_file=${preproc_dir}/filtered/_highpass0/${func_name}
        acf_prefix=acf2
        clust_prefix=psb6351_clustsim.1D
    else
        func_file=${preproc_dir}/filtered_${fwhm}mm/_highpass_${fwhm}mm0/${func_name}
        acf_prefix=acf2_${fwhm}mm
        clust_prefix=psb6351_clustsim_${fwhm}mm.1D
    fi

    # skip a kernel whose preprocessed file doesn't exist (e.g. preproc3.py not finished)
    if [ ! -f ${func_file} ]; then
        echo "** ${fwhm}mm: input not found, skipping -> ${func_file}"
        continue
    fi

    # clear this kernel's outputs from any previous run so nothing stale is left behind (not using rm)
    rm -f ${acf_prefix} ${acf_prefix}.png ${clust_prefix}.*

    #3dFWHMx COMPLETE THIS LINE...WHAT INPUTS, OUTPUTS, FLAGS DO YOU NEED.  WHAT ARE YOU TRYING TO ACCOMPLISH WITH THIS LINE?
    # WHAT: 3dFWHMx estimates how spatially smooth the data actually are. The data are smoother than the
    # applied SUSAN kernel alone (scanner point spread, interpolation during motion correction, etc.), and
    # that smoothness sets how often pure noise forms clusters by chance.
    # FLAGS:
    #   -mask     only use voxels inside the brain mask from 3dAutomask
    #   -input    the preprocessed time series (data going INTO 3dDeconvolve, not residuals)
    #   -detrend  removes polynomial trends over time first - recommended by the AFNI class 07 notes when
    #             the input is the time series rather than the 3dDeconvolve residuals (errts)
    #   -acf      fits the spatial autocorrelation function a*exp(-r*r/(2*b*b))+(1-a)*exp(-r/c) instead of a
    #             pure Gaussian. The long exponential tail is what the old Gaussian-only AlphaSim approach
    #             missed (-> inflated false positives). writes the ACF curve to acf2 (+ acf2.png)
    # OUTPUT: the last line printed is the ACF line: a  b  c  effective_FWHM -> captured for 3dClustSim
    acf_params=$(3dFWHMx -mask ${mask_file} -input ${func_file} -detrend -acf ${acf_prefix} | tail -n 1) #tail -n 1 takes the second row of output from acf
    echo "${fwhm}mm ACF params (a b c FWHM): ${acf_params}"
    read acf_a acf_b acf_c acf_fwhm <<< "${acf_params}"

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
    # ANSWER: the masked values are the ACF model parameters a, b, c (+ the effective FWHM in mm).
    #         a, b, c are what 3dClustSim -acf needs. the effective FWHM is reported but NOT passed on.
    #         5mm without -detrend (previous run): 0.587693  2.73243  7.66919    ~7.26
    #         every kernel with -detrend: see smoothness_summary.txt
    #++ ACF 1D file [radius ACF mixed_model gaussian_NEWmodel] written to acf2
    #++ 1dplot: AFNI version=AFNI_20.2.10 (Aug  4 2020) [64-bit]
    #++ Authored by: RWC et al.
    #++ and 1dplot-ed to file acf2.png

    # 3dClustSim: Monte Carlo simulation (10000 iterations by default) of noise only data with the
    # smoothness above, inside mask
    # -mask   = the SAME brain mask from 3dAutomask (WHAT GOES HERE) [[shown below]]
    # -acf    = a b c from 3dFWHMx (captured automatically above instead of copied by hand)
    # outputs = 9 tables: NN1/NN2/NN3 (faces / +edges / +corners touching) x 1sided/2sided/bisided
    3dClustSim -mask ${mask_file} -acf ${acf_a} ${acf_b} ${acf_c} -prefix ${clust_prefix}

    # pull one commonly reported threshold into the summary: NN1, 2-sided, voxelwise p = .001, alpha = .05
    # (table rows = pthr, columns = alpha .10 .05 .02 .01 -> alpha .05 is the 3rd field)
    k_clust=$(awk '!/^#/ && $1+0 == 0.001 {print $3}' ${clust_prefix}.NN1_2sided.1D)
    echo -e "${fwhm}\t${acf_a}\t${acf_b}\t${acf_c}\t${acf_fwhm}\t${k_clust}" >> ${summary_file}
done

# final summary
echo ""
echo "===== smoothness summary (also saved to ${summary_file}) ====="
cat ${summary_file}


# NOTE:
# i asked (in an earlier estimate_smoothness.sh bash) on how to automate getting the a b c outputs from acf - figured out how to do this via stackoverflow forums and claude
# my previous scripts did not utilize generative AI for help (only used it for creating the for loop here), so if this is an issue please let me know and it will not be used in the future