#!/usr/bin/env python

# class specific info account = acc_psb6351
# class specific info qos = classroom

# CHANGE YOUR SBATCH ACCORDING TO YOUR ACCESS
#SBATCH --account acc_psb6351
#SBATCH --qos classroom
#SBATCH -o /home/aoste011/psb6351_work/crash/preproc_o
#SBATCH -e /home/aoste011/psb6351_work/crash/preproc_e

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
base_dir = '/home/aoste011/Mattfeld_PSB6351'
work_dir = '/home/aoste011/psb6351_work'
sink_dir = os.path.join(base_dir, 'derivatives/preproc')
fs_dir = os.path.join(base_dir, 'derivatives/freesurfer')

# FreeSurfer setup for bbregister and the FreeSurfer nodes below
os.environ['FREESURFER_HOME'] = '/home/applications/freesurfer/7.1/freesurfer'
os.environ['PATH'] += ':/home/applications/freesurfer/7.1/freesurfer/bin/'
os.environ['SUBJECTS_DIR'] = fs_dir

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
# NOTE (my change, kept from earlier weeks): the outlier node passes in a text
#       FILE, not a list, so the function loads the file into a list first.
#       numpy is also imported inside the function because nipype Function
#       nodes run in their own environment and can't see the imports above.
def best_vol(outlier_count, middlebest):
    import numpy as np
    outlier_count = np.loadtxt(outlier_count).tolist()
    if middlebest == True:
        best_vol_num = int(np.ceil(len(outlier_count)/2)) #PICKING MIDDLE
    else:
        best_vol_num = outlier_count.index(min(outlier_count[:200]))
        if isinstance(best_vol_num, list):
            best_vol_num = best_vol_num[0]

    return best_vol_num

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
#
# MY CHANGE: I use the class account (acc_psb6351 / classroom), not acc_madlab.
#            The memory-heavy nodes below (SUSAN smoothing and temporal
#            filtering) get their own plugin_args asking for more memory.
heavy_args = {'sbatch_args': ('--account acc_psb6351 --qos classroom --mem=24G'),
              'overwrite': True}

# NODE 11: SPATIAL SMOOTHING
# You have a couple of options here...
# If you want to smooth isotropically you can use either AFNI's 3dmerge or FSL's fslmath
# For AFNI's implementation within the context of nipype check out the following page:
# https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.afni.utils.html#nipype.interfaces.afni.utils.Merge
# For FSL's implementation within the context of nipype check out hte following page:
# https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.fsl.utils.html#nipype.interfaces.fsl.utils.Smooth
# QUESTIONS TO ANSWER...
# Q1 - What does isotropic mean?
# MY ANSWER: Isotropic means being the same, regardless of which direction it is measured.
# The Gaussian kernel has the same FWHM in the x, y, and z directions. It is applied the
# same way everywhere in the brain, no matter what tissue type it is.
#
# Q2 - What are the pros and cons of isotropic spatial smoothing?
# MY ANSWER: There are many pros and cons of isotropic spatial smoothing. Some of the pros include
# that it raises SNR, because random noise averages out while real signal is spatially correlated.
# Another advantage is that it helps the overlapping of activations across subjects in group analyses.
# This helps the data fit the Gaussian Random Field assumptions, which is used for multiple comparison
# correction. It is also simple and fast. Some of the cons include it blurring tissue boundaries so signals mix. 
# This is bad as one loses spatial specificity, so that small activations tend to get washed out, separate
# regions will sometimes merge, and the peak locations can shift as well.
#
# AFNI has some cool tools to help control the final smoothness of your data
# Specifically 3dBlurToFWHM, this function will estimate your intrinsic smoothness and iteratively
# spatially blur up until it achieves a targeted smoothness
# Q3 - Why might this be good?  Are there any potential cons?
# MY ANSWER: 3dBlurToFWHM may be good to use as different sets of data start with different intrinsic smoothness 
# Blurring to a specific target means that every dataset will end at the same final smoothness. This can be very 
# beneficial when wanting to compare results across subjects and sites. The smoothness-based stats would then be 
# consistent. Some cons include it being slow, especially with the big targets. It can only add smoothness, so if 
# that data are already smoother than the target, it can not fix that. It would still blur across tissue boundaries 
# like regular smoothing does.
#
# If you intend to use AFNI's 3dBlurToFWHM check out hte following page:
# https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.afni.preprocess.html#nipype.interfaces.afni.preprocess.BlurToFWHM
# NOTE: If you elect to use this one be careful on how big you make your
# kernel as this process is iterative and can take some time
# FSL has some cool tools that help ensure that you spatially smooth like voxels
# This is FSL's SUSAN algorithm, this function will use intensities in voxels
# to constrain smoothing to like intensities (smooth only grey matter with grey matter)
# Q4 - Why might this be good? Cons (hint: begins with an 'e' and ends with 'ge' effects)?
#      How might the cons influence Gaussian Random Field Theory?
# MY ANSWER: SUSAN is good in the way that it is edge-preserving. It only averages a voxel with neighboring voxels 
# with similar brightness, so that gray matter gets smoothed with other gray matter and is not mixed with CSF or 
# white matter. Basically, with this tool, you get noise reduction while keeping spatial detail. Cons of this 
# include edge effects, that it smooths near tissue boundaries less than in the middle of the tissue. The amount 
# of smoothing varies across the brain, instead of it being uniform. This is an issue in terms of the Gaussian Random 
# Field Theory as it assumes that smoothness is the same everywhere in the image. With SUSAN this is simply not true, 
# so the multiple comparison corrections based on it can be inaccurate. 

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
# MY ANSWER: The nearest neighbor interpolation is when an image is moved into a new space. During this, each new voxel 
# takes the value of the closest original voxel, and does not average between voxels. The reason the nearest neighbor 
# interpolation may be best here is because the mask is binary, only using 0s and 1s. Other methods would average
# neighbors and create in between values, such as 0.4 along the edges, so it would not be binary anymore. Nearest neighbors 
# keep it at 0 or 1. 
#
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
# MY ANSWER (tool choice): I used FSL's SUSAN approach.

# SUSAN NODE 1: FreeSurferSource - grabs this subject's recon_all outputs
fssource = pe.Node(nio.FreeSurferSource(),
                   name='fssource')
fssource.inputs.subjects_dir = fs_dir
psb6351_wf.connect(subjID_infosource, 'subject_id', fssource, 'subject_id')

# SUSAN NODE 2: Binarize aparc+aseg (values > 0.5 = brain), dilate by 1 voxel
binarize = pe.Node(fs.Binarize(min=0.5,
                               dilate=1,
                               out_type='nii.gz'),
                   name='binarize')
psb6351_wf.connect(fssource, ('aparc_aseg', get_aparc_aseg), binarize, 'in_file')

# SUSAN NODE 3: Move the T1w-space mask into EPI space with the bbregister matrix
#   source_file = where we're going (the EPI reference volume)
#   target_file = what is moving (the binarized T1w-space mask)
#   inverse=True applies the transform from T1w space back into EPI space
masktransform = pe.Node(fs.ApplyVolTransform(inverse=True,
                                             interp='nearest'),
                        name='masktransform')
masktransform.inputs.subjects_dir = fs_dir
psb6351_wf.connect(fs_register, 'out_reg_file', masktransform, 'reg_file')
psb6351_wf.connect(binarize, 'binary_file', masktransform, 'target_file')
psb6351_wf.connect(extractref, 'roi_file', masktransform, 'source_file')

# SUSAN NODE 4: Mask each slice-time-corrected run with the EPI-space brain mask
maskfunc = pe.MapNode(fsl.ImageMaths(op_string='-mas',
                                     suffix='_brain'),
                      iterfield=['in_file'],
                      name='maskfunc')
psb6351_wf.connect(tshifter, 'out_file', maskfunc, 'in_file')
psb6351_wf.connect(masktransform, 'transformed_file', maskfunc, 'in_file2')

# SUSAN NODE 5: Median intensity inside the brain mask for each run
medianval = pe.MapNode(fsl.ImageStats(op_string='-k %s -p 50'),
                       iterfield=['in_file'],
                       name='medianval')
psb6351_wf.connect(tshifter, 'out_file', medianval, 'in_file')
psb6351_wf.connect(masktransform, 'transformed_file', medianval, 'mask_file')

# SUSAN NODE 6: Mean functional image (over time) for each masked run
meanfunc = pe.MapNode(fsl.ImageMaths(op_string='-Tmean',
                                     suffix='_mean'),
                      iterfield=['in_file'],
                      name='meanfunc')
psb6351_wf.connect(maskfunc, 'out_file', meanfunc, 'in_file')

# SUSAN NODE 7: Pair each run's mean image with its median value (hstack)
mergenode = pe.Node(util.Merge(2, axis='hstack'),
                    name='mergenode')
psb6351_wf.connect(meanfunc, 'out_file', mergenode, 'in1')
psb6351_wf.connect(medianval, 'out_stat', mergenode, 'in2')

# SUSAN NODE 8: SUSAN smoothing at 3, 6, 9, and 12mm FWHM
# NOTE: A MapNode zips its iterfield lists together one-to-one, so it can't
#       cross 4 kernels with every run by itself. Instead, the kernel list is
#       an iterable (nipype re-runs SUSAN once per kernel), and the MapNode
#       iterates over the runs.
# MY ANSWER (what else goes in the iterfield): besides in_file, the
#       brightness_threshold and usans, because each run has its own median
#       and its own mean image.
fwhm_source = pe.Node(IdentityInterface(fields=['fwhm']),
                      name='fwhm_source')
fwhm_source.iterables = ('fwhm', [8.0])

smooth = pe.MapNode(fsl.SUSAN(),
                    iterfield=['in_file', 'brightness_threshold', 'usans'],
                    name='smooth')
smooth.plugin_args = heavy_args
psb6351_wf.connect(fwhm_source, 'fwhm', smooth, 'fwhm')
psb6351_wf.connect(maskfunc, 'out_file', smooth, 'in_file')
psb6351_wf.connect(medianval, ('out_stat', getbtthresh), smooth, 'brightness_threshold')
psb6351_wf.connect(mergenode, ('out', getusans), smooth, 'usans')


# NODE 12: TEMPORAL FILTERING OR SMOOTHING
# I want you to add a node here to temporally filter the functional data --> should this be a mapnode or regular node?
# MY ANSWER: A MapNode, because there are multiple functional runs and each
#            run has to be filtered separately.
# If the functional EPI data are resting state data I want you to implement a 
# bandpass filter. If the functional EPI data are task data I want you to implement
# a highpass filter.
# Q6 - why bandpass resting state but only highpass task EPI data?
# MY ANSWER: Bandpass resting state but only highpass task EPI data because with resting state there is no task, and the signal 
# that we are looking at is typically slow spontaneous fluctuations. A bandpass removes slow drift below that range and faster noise
# above it, such as breathing and heartbeat. When it comes to task data, the task related signal can contain faster frequencies, 
# especially in event related designs, so a low pass filter can remove real task signal. This is why it is important to only remove
# the slow drift with a high pass filter whose cutoff is slower than the task's timing. 
#
# I want you to utilize either the FSL tools implementing fslmaths, what op_string flag would you need?
# MY ANSWER: -bptf <highpass sigma> <lowpass sigma>, with -1 for the lowpass
#            sigma so only the highpass filter is applied.
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

# NODES FOR TEMPORAL FILTERING GO HERE !!!!!
# These are task runs (task-study, task-loc), so I used a highpass filter
# with FSL's fslmaths -bptf.
# fslmaths wants the cutoff as a sigma in VOLUMES, not seconds:
#   sigma = cutoff / (2 * TR) = 128 s / (2 * 1.76 s) = 36.36 volumes
# -bptf also removes each voxel's mean, so the mean image is added back
# afterward (-add) to keep the data at its original intensity.
# I filtered the masked, unsmoothed runs so the effect of the filter can be
# seen on its own, separate from smoothing (this also saves disk space).
hpf_cutoff = 128.0
tr = 1.76
hpf_sigma = hpf_cutoff / (2.0 * tr)

highpass = pe.MapNode(fsl.ImageMaths(op_string='-bptf %.2f -1 -add' % hpf_sigma,
                                     suffix='_hpf'),
                      iterfield=['in_file', 'in_file2'],
                      name='highpass')
highpass.plugin_args = heavy_args
psb6351_wf.connect(maskfunc, 'out_file', highpass, 'in_file')
psb6351_wf.connect(meanfunc, 'out_file', highpass, 'in_file2')


# NODE 13: RAPID ARTIFACT DETECTION (rapidart / ArtifactDetect)
# Flags timepoints whose frame-wise displacement (FWD) is above a threshold.
# - MapNode: one run at a time; iterfield pairs each motion-corrected run
#   with its own motion parameter file from volreg (same order).
# - parameter_source='AFNI' tells rapidart the .1D columns are AFNI volreg
#   format (roll, pitch, yaw in degrees; dS, dL, dP in mm).
# - use_differences=[True, False]: the FIRST True means motion is measured
#   as the change from the previous volume (frame-wise displacement) rather
#   than distance from the reference volume. The second value is for the
#   intensity check, which stays absolute.
# - use_norm=True + norm_threshold: combines translations and rotations into
#   one composite displacement in mm and flags volumes above the threshold.
# - zintensity_threshold=3: also flags global-intensity spikes > 3 SD.
#   (The FWD counts below come from the motion part only.)
# - mask_type='file': uses the EPI-space brain mask from SUSAN NODE 3.
# Two nodes, identical except for the threshold: 1mm and 0.5mm.
def make_art(name, thresh):
    art = pe.MapNode(ra.ArtifactDetect(),
                     iterfield=['realigned_files', 'realignment_parameters'],
                     name=name)
    art.inputs.parameter_source = 'AFNI'
    art.inputs.use_differences = [True, False]
    art.inputs.use_norm = True
    art.inputs.norm_threshold = thresh
    art.inputs.zintensity_threshold = 3
    art.inputs.mask_type = 'file'
    art.inputs.save_plot = True
    psb6351_wf.connect(volreg, 'out_file', art, 'realigned_files')
    psb6351_wf.connect(volreg, 'oned_file', art, 'realignment_parameters')
    psb6351_wf.connect(masktransform, 'transformed_file', art, 'mask_file')
    return art

art_1mm = make_art('art_1mm', 1.0)
art_05mm = make_art('art_05mm', 0.5)


# NODE FINAL: DataSink. Modify to save only the files you want at the completion of your workflow
datasink = pe.Node(nio.DataSink(), name="datasink")
datasink.inputs.base_directory = sink_dir
psb6351_wf.connect(subjID_infosource, 'subject_id', datasink, 'container')
psb6351_wf.connect(extractref, 'roi_file', datasink, 'study_ref')
psb6351_wf.connect(volreg, 'out_file', datasink, 'motion.@corrfile')
psb6351_wf.connect(volreg, 'oned_matrix_save', datasink, 'motion.@matrix')
psb6351_wf.connect(volreg, 'oned_file', datasink, 'motion.@par')
psb6351_wf.connect(fs_register, 'out_reg_file', datasink, 'register.@reg_file')
psb6351_wf.connect(fs_register, 'min_cost_file', datasink, 'register.@reg_cost')
psb6351_wf.connect(fs_register, 'out_fsl_file', datasink, 'register.@reg_fsl_file')

# ADD datasink connections to save spatially smoothed and temporally filtered data
# if you implemented more than one method for diadatic purposes...save accordingly
psb6351_wf.connect(masktransform, 'transformed_file', datasink, 'mask.@epi_mask')
psb6351_wf.connect(maskfunc, 'out_file', datasink, 'masked.@unsmoothed')
psb6351_wf.connect(smooth, 'smoothed_file', datasink, 'smooth.@smoothed')
psb6351_wf.connect(highpass, 'out_file', datasink, 'hpf.@filtered')

# Rapidart outputs: outlier index lists, per-run stats, FWD values, plots
for art, folder in [(art_1mm, 'fwd1mm'), (art_05mm, 'fwd05mm')]:
    psb6351_wf.connect(art, 'outlier_files', datasink, 'art.%s.@outliers' % folder)
    psb6351_wf.connect(art, 'statistic_files', datasink, 'art.%s.@stats' % folder)
    psb6351_wf.connect(art, 'norm_files', datasink, 'art.%s.@norm' % folder)
    psb6351_wf.connect(art, 'plot_files', datasink, 'art.%s.@plots' % folder)

psb6351_wf.connect(getsubs, 'subs', datasink, 'substitutions')

psb6351_wf.config['execution']['use_relative_paths'] = True
psb6351_wf.config['execution']['crashdump_dir'] = '/home/aoste011/psb6351_work/crash'
# Each nipype job loads AFNI/FSL on the compute node itself so the cluster
# picks the builds that match that node (fixes the libpng16 error on Broadwell nodes)
slurm_template = ('#!/bin/bash\n'
                  'source /etc/profile\n'
                  'module purge\n'
                  'module load afni/25.2.07-none-none fsl/6.0.6-none-none\n')
psb6351_wf.run(plugin='SLURM',
               plugin_args={'sbatch_args': ('--account acc_psb6351 --qos classroom --mem=16G'),
                            'template': slurm_template,
                            'overwrite':True})
