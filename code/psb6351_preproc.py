#!/usr/bin/env python

# class specific info account = acc_psb6351
# class specific info qos = classroom

# CHANGE YOUR SBATCH ACCORDING TO YOUR ACCESS
#SBATCH --account acc_psb6351
#SBATCH --partition default-part
#SBATCH --qos classroom
#SBATCH -o /scratch/classroom/psb6351/mali092/Mattfeld_PSB6351/crash/preproc_o
#SBATCH -e /scratch/classroom/psb6351/mali092/Mattfeld_PSB6351/crash/preproc_e

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
base_dir = '/home/mali092/Mattfeld_PSB6351'
work_dir = '/scratch/classroom/psb6351/mali092/Mattfeld_PSB6351'
sink_dir = os.path.join(base_dir, 'derivatives/preproc')

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
                                        fmri_files='dset/%s/ses-S1/func/%s*.nii.gz',
                                        json_files='dset/%s/ses-S1/func/%s_*.json',
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

# NODE 10: Coregistration of functional to anatomical node
#          You can use what ever tool you want from what every software 
#          you want to use.  Exemplars include:
#          Freesurfer's boundary based regsitration = bbregister
#          FSL's = flirt
#          AFNI's = align_epi_anat.py
#          Reference the following webpage and the Interfaces Index
#          to determine what inputs and outputs are available
#          https://nipype.readthedocs.io/en/latest/
#          In addition to the registration files
#          How do you verify that it worked? What would you need to do?
#          What would you need to save?
#          To complete this assignment, you're going to have to add
#          a node here and modify your DataSink accordingly
#          depending on what tool you use you may need to also
#          modify the recon_all script and add a relevant directory
#          to your node (again...dependent on tool utilized).


bbregister = pe.Node(fs.BBRegister(),
                     name = 'bbregister')

bbregister.inputs.subjects_dir = '/home/mali092/Mattfeld_PSB6351/derivatives/freesurfer'
bbregister.inputs.contrast_type ='bold'
bbregister.inputs.init ='fsl'
bbregister.inputs.registered_file = True

## tells BBRegister whcih subject's Freesurfer reconstruction to use

psb6351_wf.connect(subjID_infosource, 'subject_id', bbregister, 'subject_id')

## EPI reference image for BBR

psb6351_wf.connect(extractref, 'roi_file', bbregister,'source_file')


# Add a mapnode to spatially blur the data
# save the outputs to the datasink

# NODE 11:  Register a source file to fs space and create a brain mask in source space
# The node below creates the Freesurfer source


# NODE 12: Extract aparc+aseg brain mask, binarize, and dilate by 1 voxel
## Because the background is exactly 0, while the anatomical labels are positive integers. Putting the threshold between 0 and 1 cleanly separates them


# NODE 13: Transform the binarized aparc+aseg file to the EPI space
# use a nearest neighbor interpolation



# NODE 14: Mask the functional runs with the extracted mask




# BIG NOTE: A lot of the steps that you'll start doing now require a 
#           hefty amount of memory. Your nodes may crash without very
#           interpretable error messages (e.g., RuntimeError: subprocess exited with code -9.)
#           In nipype you can control how you allocate HPC resources
#           per node using similar syntax to below:
# smooth_median.plugin_args={'sbatch_args': ('--partition highmem1-sapphirerapids --cpus-per-task=3 --account acc_madlab --qos highmem1'), 'overwrite': True}
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
### Isoptropic means equal in all spatial directions. The gaussian smoothing kernel has the same width in the x, y and z directions in isotropic spatial smoothing.
# Q2 - What are the pros and cons of isotropic spatial smoothing?
### Isotropic smoothing is commonly used in fmri analysis as it is simple and computationally efficient. It also increases the SNR by averaging the signal across neighboring voxels. It helps reduce small spatial variations between subjects. Its limitation includes blurring across tissue and anatomical boundaries as same smoothing is applied in every direction irrespective of anatomy and tissue types. 

# AFNI has some cool tools to help control the final smoothness of your data
# Specifically 3dBlurToFWHM, this function will estimate your intrinsic smoothness and iteratively
# spatially blur up until it achieves a targeted smoothness

# Q3 - Why might this be good?  Are there any potential cons?
### 3dBlurtoFWHM is good as it considers the intrinsic smoothness of the image and iteratively adds smoothing until the requested final smoothing is reached. It could have high computational cost and long processing times. If it smoothes the image excessively, it could result in a decrease in spatial specificity.

# If you intend to use AFNI's 3dBlurToFWHM check out hte following page:
# https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.afni.preprocess.html#nipype.interfaces.afni.preprocess.BlurToFWHM
# NOTE: If you elect to use this one be careful on how big you make your
# kernel as this process is iterative and can take some time
# FSL has some cool tools that help ensure that you spatially smooth like voxels
# This is FSL's SUSAN algorithm, this function will use intensities in voxels
# to constrain smoothing to like intensities (smooth only grey matter with grey matter)
# Q4 - Why might his be good? Cons (hint: begins with an 'e' and ends with 'ge' effects)?
#      How might the cons influence Gaussian Random Field Theory?
### SUSAN can better preserve anatomical boundaries because voxels with substantially different intensities contribute less to one another. This can reduce undesirable smoothing across tissue boundaries and preserve spatial specificity. Cons include edge effects which means that near the boundaries, voxels have fewer similar intensity neighbors available for smoothing. That matters for Gaussian Random Field (GRF) theory because conventional GRF-based statistical inference relies on assumptions concerning the spatial smoothness of the statistical field. If smoothing varies substantially across space, particularly around edges, those assumptions may be less well satisfied and can affect cluster-based statistical inference.

# If you choose an isotropic approach or AFNI's 3dBlurToFWHM you need
# to add just a single node here.
#
# If you choose to use the FSL SUSAN approach, you'll need to add the following
# NODE 1 - FreeSurferSource node, define subjects_dir as the project's freesurfer directory
#          and define subject_id as the subject id
fssource = pe.Node(nio.FreeSurferSource(),
                   name='fssource')
fssource.inputs.subjects_dir = '/home/mali092/Mattfeld_PSB6351/derivatives/freesurfer'

psb6351_wf.connect(subjID_infosource, 'subject_id', fssource, 'subject_id')

# NODE 2 - You will need to make a brain only mask.  I'm going to guide you to use freesurfers aparc+aseg
#          To do this you'll use freesurfer's binarize function
#          binarizing all values in the aparc+aseg file that are greater than 0.5
#          For this node to work connect the fssource node and in the connection syntax
#          imbed the get_aparc_aseg function that is already defined for you above
#          Use this node to also dilate your brian only mask in T1w space by 1 voxel

binarize = pe.Node(fs.Binarize(),
    name='binarize'
)

binarize.inputs.min = 0.5
binarize.inputs.dilate = 1

psb6351_wf.connect(fssource,
    ('aparc_aseg', get_aparc_aseg),
    binarize,
    'in_file'
)

# NODE 3 - Now you have a brain only mask in T1w space...you need to move this into the
#          EPI space by applying the volume transform from T1w space into EPI space
#          NOTE: This step is best implemented if you used Freesurfer's BBREGISTER for coregistration
#          You have to define where you're going aka 'source_file' and what is moving aka 'target_file'
#          You have to pass the registration matrix file derived from your coregistration node
#          You also have to choose an interpolation...

transform_mask = pe.Node(fs.ApplyVolTransform(),
                         name = 'transform_mask')
transform_mask.inputs.inverse = True
transform_mask.inputs.interp = 'nearest'
transform_mask.inputs.transformed_file = 'aparc_aseg_mask_epi.nii.gz'

psb6351_wf.connect(extractref, 'roi_file', transform_mask, 'source_file')
psb6351_wf.connect(binarize, 'binary_file', transform_mask, 'target_file')
psb6351_wf.connect(bbregister, 'out_reg_file', transform_mask, 'reg_file')

# Q5 - why is nearest neighbor interpolation correct here? What is nearest neighbor interpolation?
### Because nearest neighbor interpolation assigns each output voxel the value of the nearest voxel in the original image.

# NODE 4 - Now use the mask that is in EPI space to mask the EPI image by voxels that only cover the brain
#          you can use FSL's fslmaths and the '-mas' flag to work here

maskfunc = pe.MapNode(fsl.ApplyMask(),
                      iterfield=['in_file'],
                      name = 'maskfunc')
psb6351_wf.connect(tshifter, 'out_file', maskfunc, 'in_file')

psb6351_wf.connect(transform_mask, 'transformed_file', maskfunc, 'mask_file')

# NODE 5 - Get the median of your EPI data using FSL's fslmath with the following op_string = '-k %s -p 50'
median_epi = pe.MapNode(
    fsl.ImageStats(op_string='-k %s -p 50'),
    iterfield=['in_file'],
    name='median_epi'
)

psb6351_wf.connect(maskfunc, 'out_file', median_epi, 'in_file')
psb6351_wf.connect(transform_mask, 'transformed_file', median_epi, 'mask_file')

# NODE 6 - Get the mean of your EPI data using FSL's fslmath with the following op_string = '-Tmean'

mean_epi = pe.MapNode(
    fsl.MeanImage(dimension='T'),
    iterfield=['in_file'],
    name='mean_epi'
)

psb6351_wf.connect(maskfunc, 'out_file', mean_epi, 'in_file')

# NODE 7 - Use Nipype's util.Merge function to take in 2 inputs and horizontal stack the (aka., 'hstack')
#          Define your first input as the mean EPI from NODE 6 and your second input as the median EPI from NODE 5
merge = pe.Node(
    util.Merge(2, axis='hstack'),
    name='merge')

psb6351_wf.connect(mean_epi, 'out_file', merge, 'in1')
psb6351_wf.connect(median_epi, 'out_stat', merge, 'in2')

# NODE 8 - Now you have all you need to implement the SUSAN smooth node
#          Pass a list of variable smoothing kernel FWHM sizes, use a mapnode to iterate over them
#          What else needs to be in your iterfield?

susan = pe.MapNode(
    fsl.SUSAN(),
    iterfield=['in_file', 'brightness_threshold', 'usans'],
    name='susan')

susan.inputs.fwhm = 6.0

psb6351_wf.connect(maskfunc, 'out_file', susan, 'in_file')
psb6351_wf.connect(median_epi,
    ('out_stat', getbtthresh),
    susan,'brightness_threshold')

psb6351_wf.connect(merge,
    ('out', getusans),
    susan,'usans')

# NODE DATASINK - Modify your datasink node to collect the smoothed output files so you can visualize


# NODES FOR SPATIAL SMOOTHING GO HERE!!!!


# NODE 12: TEMPORAL FILTERING OR SMOOTHING
# I want you to add a node here to temporally filter the functional data --> should this be a mapnode or regular node? mapnode as we have multiple functional runs
# If the functional EPI data are resting state data I want you to implement a 
# bandpass filter. If the functional EPI data are task data I want you to implement
# a highpass filter.
# Q6 - why bandpass resting state but only highpass task EPI data?
### Because resting state fMRI uses band-pass filtering to isolate spontaneous BOLD fluctuations within a frequency range of interest, whereas task fMRI commonly uses high-pass filtering to remove slow temporal drift while preserving frequencies associated with the experimental paradigm.

# I want you to utilize either the FSL tools implementing fslmaths, what op_string flag would you need? '-bptf HIGH_PASS_SIGMA -1'
# sigma = cutt off secs/ 2* TR = 100/2*1.76 = 28.41
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
temporal_filter = pe.MapNode(fsl.ImageMaths(),
    iterfield=['in_file'],
    name='temporal_filter')

temporal_filter.inputs.op_string = '-bptf 28.41 -1'
temporal_filter.inputs.suffix = '_tempfilt'

psb6351_wf.connect(susan, 'smoothed_file',temporal_filter, 'in_file')



# NODE 7A: Rapid artifact detection for each functional run
# Detect motion outliers at two displacement thresholds: 1.0 mm and 0.5 mm.
# Both MapNodes use the motion-corrected BOLD images and AFNI motion parameters.

from nipype.algorithms.rapidart import ArtifactDetect

# Motion artifact detection at 1 mm
art_1mm = pe.MapNode(ArtifactDetect(
        parameter_source='AFNI',
        use_norm=True,
        use_differences=[True, False],
        norm_threshold=1.0,
        zintensity_threshold=3.0,
        mask_type='thresh',
        mask_threshold=0.1),
    iterfield=['realigned_files', 'realignment_parameters'],
    name='art_1mm')

psb6351_wf.connect(volreg, 'out_file', art_1mm, 'realigned_files')
psb6351_wf.connect(volreg, 'oned_file', art_1mm, 'realignment_parameters')

# Motion artifact detection at 0.5 mm
art_05mm = pe.MapNode(ArtifactDetect(
        parameter_source='AFNI',
        use_norm=True,
        use_differences=[True, False],
        norm_threshold=0.5,
        zintensity_threshold=3.0,
        mask_type='thresh',
        mask_threshold=0.1),
    iterfield=['realigned_files', 'realignment_parameters'],
    name='art_05mm')

psb6351_wf.connect(volreg, 'out_file',art_05mm, 'realigned_files')
psb6351_wf.connect(volreg, 'oned_file',art_05mm, 'realignment_parameters')



# NODE FINAL: DataSink. Modify to save only the files you want at the completion of your workflow
datasink = pe.Node(nio.DataSink(), name="datasink")
datasink.inputs.base_directory = sink_dir
psb6351_wf.connect(subjID_infosource, 'subject_id', datasink, 'container')
psb6351_wf.connect(extractref, 'roi_file', datasink, 'study_ref')
psb6351_wf.connect(volreg, 'out_file', datasink, 'motion.@corrfile')
psb6351_wf.connect(volreg, 'oned_matrix_save', datasink, 'motion.@matrix')
psb6351_wf.connect(volreg, 'oned_file', datasink, 'motion.@par')
psb6351_wf.connect(getsubs, 'subs', datasink, 'substitutions')
psb6351_wf.connect(bbregister, 'out_reg_file', datasink ,'coreg.@reg')
psb6351_wf.connect(bbregister, 'registered_file', datasink, 'coreg.@registered')
psb6351_wf.connect(transform_mask, 'transformed_file', datasink, 'coreg.@mask')
psb6351_wf.connect(maskfunc, 'out_file', datasink, 'func.@mask')
psb6351_wf.connect(susan,'smoothed_file',datasink,'func.@smoothed')
psb6351_wf.connect(temporal_filter, 'out_file', datasink, 'func.@tempfilt')
psb6351_wf.connect(art_1mm, 'norm_files', datasink, 'artifacts.@motion_1mm')
psb6351_wf.connect(art_1mm, 'outlier_files', datasink, 'artifacts.@outliers_1mm')
psb6351_wf.connect(art_1mm, 'statistic_files', datasink, 'artifacts.@stats_1mm')
psb6351_wf.connect(art_05mm, 'norm_files', datasink, 'artifacts.@motion_05mm')
psb6351_wf.connect(art_05mm, 'outlier_files', datasink, 'artifacts.@outliers_05mm')
psb6351_wf.connect(art_05mm, 'statistic_files', datasink, 'artifacts.@stats_05mm')


psb6351_wf.config['execution']['use_relative_paths'] = True
psb6351_wf.config['execution']['crashdump_dir'] = '/scratch/classroom/psb6351/mali092/Mattfeld_PSB6351/ATM/crash'
psb6351_wf.run(plugin='SLURM',
               plugin_args={'sbatch_args': ('--partition default-part --account acc_psb6351 --qos classroom --mem=8G'),
                            'overwrite':True})
