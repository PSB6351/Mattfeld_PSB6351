#!/home/umcca001/Mattfeld_PSB6351/.envs/psb6351_environment/bin/python

# class specific info account = acc_psb6351
# class specific info qos = classroom

# CHANGE YOUR SBATCH ACCORDING TO YOUR ACCESS
#SBATCH --account acc_psb6351
#SBATCH --partition default-part
#SBATCH --qos classroom
#SBATCH -o /home/umcca001/Mattfeld_PSB6351/ATM/crash/preproc_%j.out
#SBATCH -e /home/umcca001/Mattfeld_PSB6351/ATM/crash/preproc_%j.err

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

# list of subject ids
sids = ['sub-021']

# set working, base, and sink directories
base_dir = '/home/umcca001/Mattfeld_PSB6351'
work_dir = os.path.join(base_dir, 'ATM')
sink_dir = os.path.join(base_dir, 'derivatives/preproc')
fs_dir = os.path.join(base_dir, 'derivatives/freesurfer')

os.makedirs(work_dir, exist_ok=True)
os.makedirs(os.path.join(work_dir, 'crash'), exist_ok=True)
os.makedirs(sink_dir, exist_ok=True)

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

def best_vol(outlier_count, middlebest):
    import numpy as np

    counts = np.loadtxt(outlier_count).reshape(-1)

    if middlebest:
        return int(len(counts) // 2)

    return int(np.argmin(counts[:200]))

# Establish workflow and working directory
psb6351_wf = pe.Workflow(name='psb6351_wf')
psb6351_wf.base_dir = work_dir

# NODE 1: Subject iterable, re-create workflow for all subjects in list sids
subjID_infosource = pe.Node(IdentityInterface(fields=['subject_id']), name = 'subjID_infosource')
subjID_infosource.iterables = ('subject_id', sids)

# Smoothing kernel widths in millimeters.
fwhm_infosource = pe.Node(
    IdentityInterface(fields=['fwhm']),
    name='fwhm_infosource'
)
fwhm_infosource.iterables = ('fwhm', [3, 6, 9, 12])

# NODE 2: DataGrabber, currently collecting fMRI and JSON files
info = dict(
            fmri_files=[['subject_id', 'subject_id']],
            json_files=[['subject_id', 'subject_id']],
	    anat_file=[['subject_id', 'subject_id']]
          )


datasource = pe.Node(nio.DataGrabber(infields=['subject_id'], outfields=list(info.keys())),
                     name='datasource')
datasource.inputs.template = '*'
datasource.inputs.base_directory = os.path.abspath(base_dir)
datasource.inputs.field_template = dict(
                                        fmri_files='dset/%s/func/%s*.nii.gz',
                                        json_files='dset/%s/func/%s_*.json',
					anat_file='dset/%s/anat/%s_T1w.nii.gz'
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
volreg.inputs.oned_matrix_save = 'motion_matrices.1D'
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

# NODE 10: I UPDATED:
# Coregistration of functional to anatomical using FSL FLIRT
# I tried to run this node with FSL BBreg. but for some reason i didnt have access to the
#anatomical reconstruction files generated by FreeSurfer's recon-all
# I switched to FSL FLIRT so that i can  align the functional reference image to the anatomical T1 image
# w/o needing the freesurfer reconstruction outputs


# dof=6 -> 3 translations and 3 rotations (rigid-body reg)
# cost='corratio' uses the correlation ratio to eval image alignmen
# output_type='NIFTI_GZ' saves the registered image in compressed NIfTI format
coreg = pe.Node(fsl.FLIRT(dof=6, cost='corratio', output_type='NIFTI_GZ'), name='coreg')

# use the func vol ref from node 6; this is the  moving image that FLIRT will align
psb6351_wf.connect(extractref, 'roi_file', coreg, 'in_file')

#using the part. anat t1 image as the ref
# FLIRT estimates the transformation needed to align functional to anatomical space
psb6351_wf.connect(datasource, 'anat_file', coreg, 'reference')



# BIG NOTE: A lot of the steps that you'll start doing now require a
#           hefty amount of memory. Your nodes may crash without very
#           interpretable error messages (e.g., RuntimeError: subprocess exited with code -9.)
#           In nipype you can control how you allocate HPC resources
#           per node using similar syntax to below:
# smooth_median.plugin_args={'sbatch_args': ('--partition highmem1-sapphirerapids --cpus-per-task=3 --account acc_psb6351 --qos highmem1'), 'overwrite': True}
#           modify your code accordingly to excute without error

# NODE 11: SPATIAL SMOOTHING
# You have a couple of options here...
# If you want to smooth isotropically you can use either AFNI's 3dmerge or FSL's fslmath
# For AFNI's implementation within the context of nipype check out the following page:
# https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.afni.utils.html#nipype.interfaces.afni.utils.Merge
# For FSL's implementation within the context of nipype check out hte following page:
# https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.fsl.utils.html#nipype.interfaces.fsl.utils.Smooth
# QUESTIONS TO ANSWER...
# Q1 - What does isotropic mean?
# ANSWER: Isotropic means equal in all directions. For spatial smoothing,
# this means the Gaussian kernel spreads equally across the x, y, and z
# directions, rather than smoothing more in one direction than another direction


# Q2 - What are the pros and cons of isotropic spatial smoothing?

# ANSWER: Isotropic smoothing increases the signal-to-noise ratio by
# averaging neighboring voxels and can make activation patterns easier
# to detect.Also, it can  help account for small anatomical differences
# between participants. A con however is that  smoothing reduces spatial resolution
# and can blur signals across boundaries between different brain tissues
# Larger kernels produce more blurring and may alter smaller activations


# AFNI has some cool tools to help control the final smoothness of your data
# Specifically 3dBlurToFWHM, this function will estimate your intrinsic smoothness and iteratively
# spatially blur up until it achieves a targeted smoothness
# Q3 - Why might this be good?  Are there any potential cons?

# ANSWER: AFNI's 3dBlurToFWHM can be good here as it  estimates the existing spatial smoothness
# and adjusts smoothing to reach a specified FWHM. This is helpful because
# the images may already have some smoothness before additional filtering.
# A con is that the iterative process can require more computation
# and processing time than applying a Gaussian kernel directly.
# I chose FSL Smooth because it provides a simpler way to demonstrate
# the effects of the four required FWHM kernels



# If you intend to use AFNI's 3dBlurToFWHM check out hte following page:
# https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.afni.preprocess.html#nipype.interfaces.afni.preprocess.BlurToFWHM
# NOTE: If you elect to use this one be careful on how big you make your
# kernel as this process is iterative and can take some time
# FSL has some cool tools that help ensure that you spatially smooth like voxels
# This is FSL's SUSAN algorithm, this function will use intensities in voxels
# to constrain smoothing to like intensities (smooth only grey matter with grey matter)
# Q4 - Why might his be good? Cons (hint: begins with an 'e' and ends with 'ge' effects)?
#      How might the cons influence Gaussian Random Field Theory?

# ANSWER: FSL SUSAN uses voxel intensity similarities to limit smoothing
# across areas with different signal intensities and This can help  maintain the
# anatomical boundaries compared with standard Gaussian smoothing.
# However, voxels near boundaries may receive different amounts of
# smoothing than voxels within a more uniform region, creating edge effects.
# This can produce spatially varying smoothness, which may complicate the
# assumptions of stationarity used in Gaussian Random Field Theory

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
# ANSWER: Nearest-neighbor interpolation assigns each output voxel the
# value of the closest voxel in the original image. It is appropriate
# for binary brain masks because it maintains  the original label values
# of 0 and 1. Linear interpolation could create intermediate values,
# making it harder to distinguish brain from non-brain voxels
# I did not implement the SUSAN masking workflow because I used FSL Smooth

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


# I selected FSL Smooth rather than SUSAN because the assignment requires
# comparing isotropic smoothing across 3, 6, 9, and 12 mm FWHM kernels.
# FSL Smooth only requires the functional image and kernel width.
# Using fwhm_infosource allows the same six functional runs to be processed
# separately at each of the four smoothing widths.

#NODE 11:
#Smooth each functional run using the selected FWHM
smooth = pe.MapNode(
    fsl.Smooth(output_type='NIFTI_GZ'),
    iterfield=['in_file'],
    name='smooth'
)

psb6351_wf.connect(tshifter, 'out_file', smooth, 'in_file')
psb6351_wf.connect(fwhm_infosource, 'fwhm', smooth, 'fwhm')


# NODE 12: TEMPORAL FILTERING OR SMOOTHING
# I want you to add a node here to temporally filter the functional data --> should this be a mapnode or regular node?

# ANSWER: I used a MapNode because the preprocessing workflow contains
# multiple functional runs. With this, mapNode applies the same temporal filtering
# operation separately to each run rather than processing only one image

# If the functional EPI data are resting state data I want you to implement a
# bandpass filter. If the functional EPI data are task data I want you to implement
# a highpass filter.
# Q6 - why bandpass resting state but only highpass task EPI data?


# ANSWER: Resting-state analyses often focus on lower-frequency BOLD
# fluctuations, so band-pass filtering can retain a selected frequency
# range while removing slower drifts and higher-frequency noise.
# Task-based fMRI depends on signal changes associated with experimental
# events, which may contain important higher-frequency information.
# High-pass filtering removes slow scanner drift without also imposing
# a low-pass cutoff that could remove task-related signal

# I want you to utilize either the FSL tools implementing fslmaths, what op_string flag would you need?
# https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.fsl.utils.html#nipype.interfaces.fsl.utils.ImageMaths

# ANSWER: I used FSL's fslmaths through Nipype's fsl.ImageMaths interface.
# The op_string '-bptf 28.41 -1' applies temporal high-pass filtering.
# With a TR of 1.76 seconds and a 100-second cutoff, the high-pass sigma
# is 100 / (2 * 1.76) = 28.41 volumes. The -1 disables low-pass filtering so higher-frequency task-related
# signals are not additionally reduced


# Or you can use AFNI's 3dBandpass function
# https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.afni.preprocess.html#nipype.interfaces.afni.preprocess.Bandpass
# If you use AFNI's tool and you only highpass filter, how do you set your fbot and ftop?

# ANSWER: For a 100-second high-pass cutoff, fbot would be 0.01 Hz.
# To avoid removing frequencies above this cutoff, ftop would need to
# reach the Nyquist frequency, approximately 0.284 Hz for TR = 1.76 s,
# subject to the interface's permitted settings
# I used FSL ImageMaths instead, so these AFNI parameters were not needed


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




# I used FSL ImageMaths to high-pass filter the task-based functional data.
# The 100-second cutoff reduces slow temporal fluctuations while preserving
# higher-frequency information that may be relevant to task responses

# NODE 12: High-pass filtering using FSL
highpass = pe.MapNode(fsl.ImageMaths(op_string='-bptf 28.41 -1'),
                      iterfield=['in_file'],
                      name='highpass')
psb6351_wf.connect(smooth, 'smoothed_file', highpass, 'in_file')



# NODE FINAL: DataSink. Modify to save only the files you want at the completion of your workflow
datasink = pe.Node(nio.DataSink(), name="datasink")
datasink.inputs.base_directory = sink_dir

psb6351_wf.connect(subjID_infosource, 'subject_id', datasink, 'container')
psb6351_wf.connect(extractref, 'roi_file', datasink, 'study_ref')
# Save the motion-corrected functional images from AFNI Volreg
psb6351_wf.connect(volreg, 'out_file', datasink, 'motion.@corrfile')
psb6351_wf.connect(volreg, 'oned_matrix_save', datasink, 'motion.@matrix')
psb6351_wf.connect(volreg, 'oned_file', datasink, 'motion.@par')

# Save the outputs from FSL FLIRT instead of FreeSurfer BBReg
# FLIRT makes a reg functional image and  transformation matrix
# The registered image allows us to check alignment in FSLeyes
# The matrix stores the rotations and translations used for coregistration
# Both outputs are saved in DataSink
psb6351_wf.connect(coreg, 'out_file', datasink, 'register.@registered_file')
psb6351_wf.connect(coreg, 'out_matrix_file', datasink, 'register.@transform_matrix')

# Save spatially smoothed and temporally filtered data
# Save spatially smoothed images for all four FWHM kernels
# FSL Smooth produces 'smoothed_file', not 'out_file'
psb6351_wf.connect(smooth, 'smoothed_file', datasink, 'smooth.@blurred')
psb6351_wf.connect(highpass, 'out_file', datasink, 'filter.@highpass')

psb6351_wf.connect(getsubs, 'subs', datasink, 'substitutions')


# Run the preprocessing workflow using SLURM on the HPC
# SLURM submits the processing nodes as jobs on the cluster
psb6351_wf.run(plugin='SLURM', plugin_args={'sbatch_args': '--partition default-part --account acc_psb6351 --qos classroom --mem=8G', 'overwrite': True})
