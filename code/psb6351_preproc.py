#!/usr/bin/env python

# class specific info account = acc_psb6351
# class specific info qos = classroom

#SBATCH --account acc_psb6351
#SBATCH --qos classroom
#SBATCH -o /home/cbeac004/Mattfeld_PSB6351/preproc_assignment/crash/preproc_o
#SBATCH -e /home/cbeac004/Mattfeld_PSB6351/preproc_assignment/crash/preproc_e

import os
from glob import glob

# Import new things that we'll need
import pandas as pd
import numpy as np
import nipype.interfaces.afni as afni
import nipype.interfaces.fsl as fsl
import nipype.interfaces.freesurfer as fs
from nipype.interfaces.utility import Function, IdentityInterface
import nibabel as nb
import json
import nipype.interfaces.io as nio
import nipype.pipeline.engine as pe 
import nipype.interfaces.utility as util
import nipype.algorithms.rapidart as ra

# list of subject ids
sids = ['sub-021']

# set working, base, and sink directories
base_dir = '/home/cbeac004/Mattfeld_PSB6351'
work_dir = '/home/cbeac004/Mattfeld_PSB6351/preproc_assignment'
sink_dir = os.path.join(base_dir, 'derivatives/preproc')
fs_dir = '/home/amattfel/Mattfeld_PSB6351/derivatives/freesurfer'

# Set to True to use FreeSurfer (bbregister + aparc+aseg brain mask).
# I don't have read access to the FreeSurfer outputs above yet, so for now the
# brain mask is made directly from the EPI reference volume with AFNI's 3dAutomask.
use_freesurfer = False

# Function for extracting slice timing info from fMRI json sidecars
def slc_time(json_file_list):
    import json
    slice_timing_list = []
    for curr_json in json_file_list:
        curr_json_data = open(curr_json)
        curr_func_metadata = json.load(curr_json_data)
        slice_timing_list.append(curr_func_metadata['SliceTiming'])

    return slice_timing_list

# Function for substitutions. Relevant for DataSink
def get_subs(subject_id):
    '''Produces Name Substitutions for Each Contrast'''
    subs = [('_subject_id_%s'%subject_id, '')]
    return subs

# The following two fucntions will be necessary
# for the spatial blurring/smoothing out of class work
# particularly if you intend to use the FSL SUSAN algorithm
# https://web.mit.edu/fsl_v5.0.10/fsl/doc/wiki/SUSAN.html
def getbtthresh(medianvals):
    """Get the brightness threshold for SUSAN."""
    return [0.75*val for val in medianvals]

def getusans(inlist):
    """Return the usans at the right threshold."""
    return [[tuple([val[0],0.75*val[1]])] for val in inlist]

# Function for grabbing aparc+aseg file from fssource node
def get_aparc_aseg(files):
    for name in files:
        if 'aparc+aseg' in name:
            return name
    raise ValueError('aparc+aseg.mgz not found')

# Function for grabbing the first item in a list
def pickfirst(func):
    if isinstance(func, list):
        return func[0]
    else:
        return func

# Function for picking the best volume derived from a 
# list of outlier counts
def best_vol(outlier_count, middlebest):
    if middlebest == True:
        best_vol_num = int(np.ceil(len(outlier_count)/2)) #PICKING MIDDLE
    else:
        best_vol_num = outlier_count.index(min(outlier_count[:200]))
        if isinstance(best_vol_num, list):
            best_vol_num = best_vol_num[0]

    return best_vol_num

# Function for counting outlier timepoints in each run from rapidart outputs.
# norm_files hold the frame-wise displacement (FWD, mm) for every timepoint
# (rapidart's composite norm, frame differenced because use_differences[0]=True),
# so counting values above the threshold gives the number of FWD outliers.
# outlier_files hold every timepoint rapidart flagged (FWD + intensity outliers).
# Writes one csv per threshold with a row per run.
def count_outliers(norm_files, outlier_files, threshold):
    import os
    import numpy as np
    import pandas as pd
    rows = []
    for run_num, (norm_file, outlier_file) in enumerate(zip(norm_files, outlier_files)):
        fwd = np.atleast_1d(np.loadtxt(norm_file))
        if os.path.getsize(outlier_file) > 0:
            all_outliers = np.atleast_1d(np.loadtxt(outlier_file))
        else:
            all_outliers = np.array([])
        rows.append({'run': run_num + 1,
                     'func_file': os.path.basename(norm_file).replace('norm.', '').replace('.txt', ''),
                     'fwd_threshold_mm': threshold,
                     'n_timepoints': len(fwd),
                     'n_fwd_outliers': int(np.sum(fwd > threshold)),
                     'n_total_art_outliers': len(all_outliers),
                     'mean_fwd_mm': float(np.mean(fwd)),
                     'max_fwd_mm': float(np.max(fwd))})
    out_file = os.path.abspath('outlier_counts_fwd%smm.csv' % str(threshold).replace('.', 'p'))
    pd.DataFrame(rows).to_csv(out_file, index=False)
    print(pd.DataFrame(rows).to_string(index=False))
    return out_file

# Establish workflow and working directory
psb6351_wf = pe.Workflow(name='psb6351_wf')
psb6351_wf.base_dir = work_dir

# NODE 1: Subject iterable, re-create workflow for all subjects in list sids
subjID_infosource = pe.Node(IdentityInterface(fields=['subject_id']), name = 'subjID_infosource')
subjID_infosource.iterables = ('subject_id', sids)

# NODE 2: DataGrabber, currently collecting fMRI and JSON files
info = dict(
            fmri_files=[['subject_id', 'subject_id']],
            json_files=[['subject_id', 'subject_id']],
           )

datasource = pe.Node(nio.DataGrabber(infields=['subject_id'], outfields=list(info.keys())),
                     name='datasource')
datasource.inputs.template = '*'
datasource.inputs.base_directory = os.path.abspath(base_dir)
datasource.inputs.field_template = dict(
                                        fmri_files='dset/%s/func/%s*.nii.gz',
                                        json_files='dset/%s/func/%s_*.json',
                                       )
datasource.inputs.template_args = info
datasource.inputs.sort_filelist = True
datasource.inputs.raise_on_empty = True
psb6351_wf.connect(subjID_infosource, 'subject_id', datasource, 'subject_id')

# NODE 3: Substitution function to be used with DataSink 
getsubs = pe.Node(Function(input_names=['subject_id'],
                           output_names=['subs'],
                           function=get_subs),
                  name='getsubs')
psb6351_wf.connect(subjID_infosource, 'subject_id', getsubs, 'subject_id')    

# NODE 4: Identify number of outliers in the
#         first fMRI run (note applciation of pickfirst fxn)
id_outliers = pe.Node(afni.OutlierCount(),
                      name = 'id_outliers')
id_outliers.inputs.automask = True
id_outliers.inputs.legendre = True
id_outliers.inputs.polort = 4
id_outliers.inputs.out_file = 'outlier_file'
psb6351_wf.connect(datasource, ('fmri_files', pickfirst), id_outliers, 'in_file')

# NODE 5: Pass outlier text file to this function to pick best volume
getbestvol = pe.Node(Function(input_names=['outlier_count', 'middlebest'],
                              output_names=['best_vol_num'],
                              function=best_vol),
                     name='getbestvol')
getbestvol.inputs.middlebest = False
psb6351_wf.connect(id_outliers, 'out_file', getbestvol, 'outlier_count')

# NODE 6: Use FSL tool to isolate/extract best volume
extractref = pe.Node(fsl.ExtractROI(t_size=1),
                     name = "extractref")
psb6351_wf.connect(getbestvol, 'best_vol_num', extractref, 't_min')
psb6351_wf.connect(datasource, ('fmri_files', pickfirst), extractref, 'in_file')

# NODE 7: Motion correction node - NOTE Applying this before slicetimeing
volreg = pe.MapNode(afni.Volreg(),
                    iterfield=['in_file'],
                    name = 'volreg')
volreg.inputs.outputtype = 'NIFTI_GZ'
volreg.inputs.zpad = 4
psb6351_wf.connect(extractref, 'roi_file', volreg, 'basefile')
psb6351_wf.connect(datasource, 'fmri_files', volreg, 'in_file')

# NODE 7b: Rapid artifact detection (rapidart) over all functional runs
# https://nipype.readthedocs.io/en/latest/api/generated/nipype.algorithms.rapidart.html
# Uses the motion corrected runs and AFNI's 3dvolreg motion parameters
# (parameter_source='AFNI' tells rapidart the column order/units of the .1D file).
# norm_threshold is the frame-wise displacement (FWD) cutoff in mm.
# use_differences=[True, False] -> motion is frame-to-frame (FWD), intensity is not.
# zintensity_threshold flags timepoints whose global signal is > 3 SD from the mean.
# It's a MapNode so every run gets its own outlier file.
# One node per threshold (1mm and 0.5mm) instead of iterables so the
# smoothing/filtering branches below aren't duplicated for each threshold.
fwd_thresholds = [1.0, 0.5]
art_nodes = {}
for thresh in fwd_thresholds:
    thresh_name = str(thresh).replace('.', 'p')
    art = pe.MapNode(ra.ArtifactDetect(),
                     iterfield=['realigned_files', 'realignment_parameters'],
                     name='art_fwd%smm' % thresh_name)
    art.inputs.parameter_source = 'AFNI'
    art.inputs.use_differences = [True, False]
    art.inputs.use_norm = True
    art.inputs.norm_threshold = thresh
    art.inputs.zintensity_threshold = 3
    art.inputs.mask_type = 'spm_global'
    art.inputs.save_plot = True
    art.plugin_args = {'sbatch_args': '--account acc_psb6351 --qos classroom --mem=16G', 'overwrite': True}
    psb6351_wf.connect(volreg, 'out_file', art, 'realigned_files')
    psb6351_wf.connect(volreg, 'oned_file', art, 'realignment_parameters')

    # Count the outlier timepoints for each run at this threshold
    countart = pe.Node(Function(input_names=['norm_files', 'outlier_files', 'threshold'],
                                output_names=['count_file'],
                                function=count_outliers),
                       name='count_outliers_fwd%smm' % thresh_name)
    countart.inputs.threshold = thresh
    psb6351_wf.connect(art, 'norm_files', countart, 'norm_files')
    psb6351_wf.connect(art, 'outlier_files', countart, 'outlier_files')
    art_nodes[thresh_name] = (art, countart)

# NODE 8: Get list of slice times from JSON files.
getslctime = pe.Node(Function(input_names=['json_file_list'],
                              output_names=['slctime_list'],
                              function=slc_time),
                     name='getslctime')
psb6351_wf.connect(datasource, 'json_files', getslctime, 'json_file_list')

# NODE 9: Slicetiming correction node - applied after motion correction
#         list of fMRI files must equal list of slice_timing derived from JSONs
tshifter = pe.MapNode(afni.TShift(),
                      iterfield=['in_file','slice_timing'],
                      name = 'tshifter')
tshifter.inputs.tr = '1.76'
tshifter.inputs.outputtype = 'NIFTI_GZ'
psb6351_wf.connect(volreg, 'out_file', tshifter, 'in_file')
psb6351_wf.connect(getslctime, 'slctime_list', tshifter, 'slice_timing')

# NODE 10: Coregistration of functional to anatomical node using freesurfer's bbregister
#          (only when use_freesurfer is True)
if use_freesurfer:
    fs_register = pe.Node(fs.BBRegister(init='fsl'),
                          name ='fs_register')
    fs_register.inputs.contrast_type = 't2'
    fs_register.inputs.out_fsl_file = True
    fs_register.inputs.subjects_dir = fs_dir
    psb6351_wf.connect(subjID_infosource, 'subject_id', fs_register, 'subject_id')
    psb6351_wf.connect(extractref, 'roi_file', fs_register, 'source_file')

# BIG NOTE: A lot of the steps that you'll start doing now require a 
#           hefty amount of memory. Your nodes may crash without very
#           interpretable error messages (e.g., RuntimeError: subprocess exited with code -9.)
#           In nipype you can control how you allocate HPC resources
#           per node using similar syntax to below:
# smooth_median.plugin_args={'sbatch_args': ('--partition highmem1-sapphirerapids --cpus-per-task=3 --account acc_madlab --qos highmem1'), 'overwrite': True}
#           modify your code accordingly to excute without error
# Resources requested for the memory heavy nodes below (class account/qos)
# If nodes still die with code -9 bump up --mem
highmem_args = {'sbatch_args': ('--account acc_psb6351 --qos classroom --cpus-per-task=2 --mem=16G'),
                'overwrite': True}

# Smoothing kernels (FWHM in mm) to compare, per the syllabus
fwhm_list = [3, 6, 9, 12]

# NODE 11: SPATIAL SMOOTHING
# You have a couple of options here...
# If you want to smooth isotropically you can use either AFNI's 3dmerge or FSL's fslmath
# For AFNI's implementation within the context of nipype check out the following page:
# https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.afni.utils.html#nipype.interfaces.afni.utils.Merge
# For FSL's implementation within the context of nipype check out hte following page:
# https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.fsl.utils.html#nipype.interfaces.fsl.utils.Smooth
# QUESTIONS TO ANSWER...
# Q1 - What does isotropic mean?
#      A: Isotropic means the same in every direction. So an isotropic 6mm kernel
#         blurs 6mm in x, y, and z equally, instead of blurring more in one direction
#         than another.
# Q2 - What are the pros and cons of isotropic spatial smoothing?
#      A: The main pro is that smoothing averages out random noise, so the signal to
#         noise ratio goes up. It also helps at the group level because everyone's
#         brain is a little different, and blurring makes activations line up better
#         across subjects. Smoothing also makes the data fit the assumptions of
#         Gaussian random field theory better, and it's simple and easy to report.
#         The cons are that you lose spatial resolution. Small activations can get
#         washed out and two nearby activations can blend into one. Since it's
#         isotropic it doesn't care about anatomy, so grey matter gets blurred with
#         white matter, CSF, and even voxels outside the brain. Picking the kernel
#         size is also kind of arbitrary, and too much smoothing could hurt MVPA
#         type analyses that depend on fine grained patterns.
# AFNI has some cool tools to help control the final smoothness of your data
# Specifically 3dBlurToFWHM, this function will estimate your intrinsic smoothness and iteratively
# spatially blur up until it achieves a targeted smoothness
# Q3 - Why might this be good?  Are there any potential cons?
#      A: This is nice because everyone ends up with the same final smoothness.
#         If you just apply a 6mm kernel, it gets added on top of however smooth the
#         data already were, and that differs between subjects, runs, and scanners.
#         The downsides are that it's slow since it keeps iterating, and the target
#         has to be bigger than the smoothest dataset you have. It also depends on
#         estimating smoothness, which can be thrown off by motion or artifacts,
#         and it still smooths across tissue types like regular Gaussian smoothing.
# If you intend to use AFNI's 3dBlurToFWHM check out hte following page:
# https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.afni.preprocess.html#nipype.interfaces.afni.preprocess.BlurToFWHM
# NOTE: If you elect to use this one be careful on how big you make your
# kernel as this process is iterative and can take some time
# FSL has some cool tools that help ensure that you spatially smooth like voxels
# This is FSL's SUSAN algorithm, this function will use intensities in voxels
# to constrain smoothing to like intensities (smooth only grey matter with grey matter)
# Q4 - Why might his be good? Cons (hint: begins with an 'e' and ends with 'ge' effects)?
#      How might the cons influence Gaussian Random Field Theory?
#      A: SUSAN is good because it only averages together voxels with similar
#         intensity, so you still get the noise reduction but grey matter signal
#         doesn't bleed into white matter or CSF. The con is edge effects. 
#	  Gaussian random field theory assumes the smoothness is uniform and
#         can be estimated, so with SUSAN those estimates could be off and the
#         corrected thresholds could end up too strict in some places and too
#         lenient in others.
#
# If you choose an isotropic approach or AFNI's 3dBlurToFWHM you need
# to add just a single node here.
#
# If you choose to use the FSL SUSAN approach, you'll need to add the following
# NODE 1 - FreeSurferSource node, define subjects_dir as the project's freesurfer directory
#          and define subject_id as the subject id
# NODE 2 - You will need to make a brain only mask.  I'm going to guide you to use freesurfers aparc+aseg
#          To do this you'll use freesurfer's binarize function
#          binarizing all values in the aparc+aseg file that are greater than 0.5
#          For this node to work connect the fssource node and in the connection syntax
#          imbed the get_aparc_aseg function that is already defined for you above
#          Use this node to also dilate your brian only mask in T1w space by 1 voxel
# NODE 3 - Now you have a brain only mask in T1w space...you need to move this into the
#          EPI space by applying the volume transform from T1w space into EPI space
#          NOTE: This step is best implemented if you used Freesurfer's BBREGISTER for coregistration
#          You have to define where you're going aka 'source_file' and what is moving aka 'target_file'
#          You have to pass the registration matrix file derived from your coregistration node
#          You also have to choose an interpolation...
# Q5 - why is nearest neighbor interpolation correct here? What is nearest neighbor interpolation?
#      A: Nearest neighbor interpolation just gives each new voxel the value of
#         whichever original voxel is closest, instead of averaging nearby voxels
#         like trilinear or sinc interpolation does. Our mask only has 0s and 1s,
#         and we want to keep it that way. Nearest neighbor can
#         only output values that were already in the image, so it stays 0 or 1.
# NODE 4 - Now use the mask that is in EPI space to mask the EPI image by voxels that only cover the brain
#          you can use FSL's fslmaths and the '-mas' flag to work here
# NODE 5 - Get the median of your EPI data using FSL's fslmath with the following op_string = '-k %s -p 50'
# NODE 6 - Get the mean of your EPI data using FSL's fslmath with the following op_string = '-Tmean'
# NODE 7 - Use Nipype's util.Merge function to take in 2 inputs and horizontal stack the (aka., 'hstack')
#          Define your first input as the mean EPI from NODE 6 and your second input as the median EPI from NODE 5
# NODE 8 - Now you have all you need to implement the SUSAN smooth node
#          Pass a list of variable smoothing kernel FWHM sizes, use a mapnode to iterate over them
#          What else needs to be in your iterfield?
# NODE DATASINK - Modify your datasink node to collect the smoothed output files so you can visualize


# NODES FOR SPATIAL SMOOTHING GO HERE!!!!
# I chose the FSL SUSAN approach

if use_freesurfer:
    # SUSAN NODE 1: FreeSurferSource to grab the subject's recon-all outputs
    fssource = pe.Node(nio.FreeSurferSource(),
                       name='fssource')
    fssource.inputs.subjects_dir = fs_dir
    psb6351_wf.connect(subjID_infosource, 'subject_id', fssource, 'subject_id')

    # SUSAN NODE 2: Binarize the aparc+aseg (> 0.5) to get a brain only mask
    #               in T1w space and dilate it by 1 voxel
    fs_threshold = pe.Node(fs.Binarize(min=0.5, dilate=1, out_type='nii.gz'),
                           name='fs_threshold')
    psb6351_wf.connect(fssource, ('aparc_aseg', get_aparc_aseg), fs_threshold, 'in_file')

    # SUSAN NODE 3: Move the brain mask from T1w space into EPI space
    #               bbregister registered EPI -> T1w, so apply the inverse.
    #               source_file = where we are going (EPI reference volume)
    #               target_file = what is moving (T1w brain mask)
    fs_voltransform = pe.Node(fs.ApplyVolTransform(inverse=True, interp='nearest'),
                              name='fs_voltransform')
    fs_voltransform.inputs.subjects_dir = fs_dir
    psb6351_wf.connect(extractref, 'roi_file', fs_voltransform, 'source_file')
    psb6351_wf.connect(fs_register, 'out_reg_file', fs_voltransform, 'reg_file')
    psb6351_wf.connect(fs_threshold, 'binary_file', fs_voltransform, 'target_file')
    mask_node, mask_field = fs_voltransform, 'transformed_file'
else:
    # Without FreeSurfer: make the brain mask straight from the EPI reference
    # volume with AFNI's 3dAutomask (dilated by 1 voxel). Every run was motion
    # corrected to this volume, so the mask is already in EPI space and no
    # transform/interpolation is needed.
    automask = pe.Node(afni.Automask(outputtype='NIFTI_GZ', dilate=1),
                       name='automask')
    psb6351_wf.connect(extractref, 'roi_file', automask, 'in_file')
    mask_node, mask_field = automask, 'out_file'

# SUSAN NODE 4: Mask each motion + slicetime corrected run with the EPI space brain mask
maskfunc = pe.MapNode(fsl.ImageMaths(op_string='-mas', suffix='_bet'),
                      iterfield=['in_file'],
                      name='maskfunc')
maskfunc.plugin_args = highmem_args
psb6351_wf.connect(tshifter, 'out_file', maskfunc, 'in_file')
psb6351_wf.connect(mask_node, mask_field, maskfunc, 'in_file2')

# SUSAN NODE 5: Median value within the brain mask for each run
#               (fslstats -k mask -p 50)
medianval = pe.MapNode(fsl.ImageStats(op_string='-k %s -p 50'),
                       iterfield=['in_file'],
                       name='medianval')
medianval.plugin_args = highmem_args
psb6351_wf.connect(tshifter, 'out_file', medianval, 'in_file')
psb6351_wf.connect(mask_node, mask_field, medianval, 'mask_file')

# SUSAN NODE 6: Mean functional image for each masked run
meanfunc = pe.MapNode(fsl.ImageMaths(op_string='-Tmean', suffix='_mean'),
                      iterfield=['in_file'],
                      name='meanfunc')
meanfunc.plugin_args = highmem_args
psb6351_wf.connect(maskfunc, 'out_file', meanfunc, 'in_file')

# SUSAN NODE 7: Pair each run's mean image with its median value
#               hstack -> [(mean_run1, median_run1), (mean_run2, median_run2), ...]
mergenode = pe.Node(util.Merge(2, axis='hstack'),
                    name='mergenode')
psb6351_wf.connect(meanfunc, 'out_file', mergenode, 'in1')
psb6351_wf.connect(medianval, 'out_stat', mergenode, 'in2')

# SUSAN NODE 8: SUSAN smoothing
#               brightness threshold = 75% of each run's median (getbtthresh)
#               usans = the run's mean image with the same 75% threshold (getusans)
#               The iterfield needs everything that is run-specific: the run itself,
#               its brightness threshold, and its usan. The FWHM kernels are the same
#               for every run, so they are iterated with iterables (3, 6, 9, 12mm)
#               which re-runs SUSAN on all runs once per kernel.
smooth = pe.MapNode(fsl.SUSAN(),
                    iterfield=['in_file', 'brightness_threshold', 'usans'],
                    name='smooth')
smooth.iterables = ('fwhm', fwhm_list)
smooth.plugin_args = highmem_args
psb6351_wf.connect(maskfunc, 'out_file', smooth, 'in_file')
psb6351_wf.connect(medianval, ('out_stat', getbtthresh), smooth, 'brightness_threshold')
psb6351_wf.connect(mergenode, ('out', getusans), smooth, 'usans')


# NODE 12: TEMPORAL FILTERING OR SMOOTHING
# I want you to add a node here to temporally filter the functional data --> should this be a mapnode or regular node?
# If the functional EPI data are resting state data I want you to implement a 
# bandpass filter. If the functional EPI data are task data I want you to implement
# a highpass filter.
# Q6 - why bandpass resting state but only highpass task EPI data?
# I want you to utilize either the FSL tools implementing fslmaths, what op_string flag would you need?
# https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.fsl.utils.html#nipype.interfaces.fsl.utils.ImageMaths
# Or you can use AFNI's 3dBandpass function
# https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.afni.preprocess.html#nipype.interfaces.afni.preprocess.Bandpass
# If you use AFNI's tool and you only highpass filter, how do you set your fbot and ftop?
# If you are electing to use the Discrete Cosine Tranforms (DCTs) to statistically account for low frequency noise
# you'll need to run a regression model.
# For this step I would recommend utilizing AFNI's 3dDeconvolve paired with 3dREMLfit
# First using 3dDeconvolve you'll need to 
# define your legendre input as True and your number of polorts as an integer - try 7..
# you can also make the x1D_stop flag True as you don't need to run the 3dDeconvolve as 3dREMLfit does the heavy lifting here
# create another node for the 3dREMLfit passing the x1D matrix from the 3dDeconvolve node and save in your datasink the residuals
# https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.afni.model.html#nipype.interfaces.afni.model.Deconvolve
# 
# If you're feeling ambitious you can implement multiple approaches and compare/contrast them
#
# Q6 answer: Both kinds of data have slow drift from things like scanner heating and
# physiology, so both need a highpass filter. With resting state, the signal we care
# about is the slow spontaneous fluctuations (around 0.01-0.1 Hz), so anything faster
# than that, like cardiac and breathing noise, can be filtered out too, which is why
# it gets a bandpass. With task data the signal we care about is the response to the
# task, and depending on the design (especially event-related designs) some of that
# signal is at higher frequencies. A lowpass filter could remove real task signal,
# and the GLM already deals with high frequency noise, so we only highpass.
#
# Our runs (task-loc and task-study) are task data, so I only highpass filtered.
# I used fslmaths -bptf with the lowpass sigma set to -1 so it's turned off.
# The sigma is in volumes, not seconds: sigma = cutoff / (2 * TR). I went with
# FSL's default 100s cutoff, so sigma = 100 / (2 * 1.76) = 28.41 volumes, which
# removes anything slower than 0.01 Hz.
# I made it a MapNode because fslmaths works on one run at a time and we have
# several runs.
# Newer versions of FSL remove the mean of each voxel when you use -bptf, so I add
# the mean image back in after filtering.

# NODES FOR TEMPORAL FILTERING GO HERE !!!!!
hp_cutoff = 100.
tr = 1.76
hp_sigma = hp_cutoff / (2 * tr)

# Mean of each smoothed run, to add back after filtering
meansmooth = pe.MapNode(fsl.ImageMaths(op_string='-Tmean', suffix='_mean'),
                        iterfield=['in_file'],
                        name='meansmooth')
meansmooth.plugin_args = highmem_args
psb6351_wf.connect(smooth, 'smoothed_file', meansmooth, 'in_file')

# Highpass filter each smoothed run (runs for every kernel because of the
# fwhm iterables upstream)
highpass = pe.MapNode(fsl.ImageMaths(op_string='-bptf %.10f -1 -add' % hp_sigma,
                                     suffix='_tempfilt'),
                      iterfield=['in_file', 'in_file2'],
                      name='highpass')
highpass.plugin_args = highmem_args
psb6351_wf.connect(smooth, 'smoothed_file', highpass, 'in_file')
psb6351_wf.connect(meansmooth, 'out_file', highpass, 'in_file2')

# NODE FINAL: DataSink. Modify to save only the files you want at the completion of your workflow
datasink = pe.Node(nio.DataSink(), name="datasink")
datasink.inputs.base_directory = sink_dir
psb6351_wf.connect(subjID_infosource, 'subject_id', datasink, 'container')
psb6351_wf.connect(extractref, 'roi_file', datasink, 'study_ref')
psb6351_wf.connect(volreg, 'out_file', datasink, 'motion.@corrfile')
psb6351_wf.connect(volreg, 'oned_matrix_save', datasink, 'motion.@matrix')
psb6351_wf.connect(volreg, 'oned_file', datasink, 'motion.@par')
# rapidart outputs, one folder per FWD threshold
for thresh_name, (art, countart) in art_nodes.items():
    art_dir = 'art.fwd%smm' % thresh_name
    psb6351_wf.connect(art, 'outlier_files', datasink, art_dir + '.@outlier_files')
    psb6351_wf.connect(art, 'norm_files', datasink, art_dir + '.@norm_files')
    psb6351_wf.connect(art, 'statistic_files', datasink, art_dir + '.@stat_files')
    psb6351_wf.connect(art, 'plot_files', datasink, art_dir + '.@plot_files')
    psb6351_wf.connect(countart, 'count_file', datasink, art_dir + '.@counts')
if use_freesurfer:
    psb6351_wf.connect(fs_register, 'out_reg_file', datasink, 'register.@reg_file')
    psb6351_wf.connect(fs_register, 'min_cost_file', datasink, 'register.@reg_cost')
    psb6351_wf.connect(fs_register, 'out_fsl_file', datasink, 'register.@reg_fsl_file')

# ADD datasink connections to save spatially smoothed and temporally filtered data
# if you implemented more than one method for diadatic purposes...save accordingly
# Smoothed and filtered outputs land in a _fwhm_<size> folder per kernel
psb6351_wf.connect(mask_node, mask_field, datasink, 'mask.@epi_mask')
psb6351_wf.connect(maskfunc, 'out_file', datasink, 'masked_func')
psb6351_wf.connect(smooth, 'smoothed_file', datasink, 'smooth')
psb6351_wf.connect(highpass, 'out_file', datasink, 'hpfilter')

psb6351_wf.connect(getsubs, 'subs', datasink, 'substitutions')

psb6351_wf.config['execution']['use_relative_paths'] = True
psb6351_wf.config['execution']['crashdump_dir'] = '/home/cbeac004/Mattfeld_PSB6351/preproc_assignment/crash'
psb6351_wf.run(plugin='SLURM',
               plugin_args={'sbatch_args': ('--account acc_psb6351 --qos classroom'),
                            'overwrite':True})
