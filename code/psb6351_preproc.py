#!/usr/bin/env python

# class specific info account = acc_psb6351
# class specific info qos = classroom

#SBATCH --account acc_madlab
#SBATCH --partition highmem1-sapphirerapids
#SBATCH --qos highmem1
#SBATCH -o /scratch/madlab/Mattfeld_PSB6351/ATM/crash/preproc_o
#SBATCH -e /scratch/madlab/Mattfeld_PSB6351/ATM/crash/preproc_e

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
base_dir = '/home/amattfel/Mattfeld_PSB6351'
work_dir = '/scratch/madlab/Mattfeld_PSB6351/ATM'
sink_dir = os.path.join(base_dir, 'derivatives/preproc')
fs_dir = '/home/amattfel/Mattfeld_PSB6351/derivatives/freesurfer'

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

# Functions for SUSAN
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

# NODE 11 (comprised of multiple nodes): SPATIAL SMOOTHING
# The node below creates the Freesurfer source
fssource = pe.Node(nio.FreeSurferSource(),
                   name ='fssource')
fssource.inputs.subjects_dir = fs_dir
psb6351_wf.connect(subjID_infosource, 'subject_id', fssource, 'subject_id')

# Extract aparc+aseg brain mask, binarize, and dilate by 1 voxel
fs_threshold = pe.Node(fs.Binarize(min=0.5, out_type='nii'),
                       name ='fs_threshold')
fs_threshold.inputs.dilate = 1
psb6351_wf.connect(fssource, ('aparc_aseg', get_aparc_aseg), fs_threshold, 'in_file')

# Transform the binarized aparc+aseg file to the EPI space
# use a nearest neighbor interpolation
fs_voltransform = pe.Node(fs.ApplyVolTransform(inverse=True),
                          name='fs_transform')
fs_voltransform.inputs.subjects_dir = fs_dir
fs_voltransform.inputs.interp = 'nearest'
psb6351_wf.connect(extractref, 'roi_file', fs_voltransform, 'source_file')
psb6351_wf.connect(fs_register, 'out_reg_file', fs_voltransform, 'reg_file')
psb6351_wf.connect(fs_threshold, 'binary_file', fs_voltransform, 'target_file')

# Mask the functional runs with the extracted mask
maskfunc = pe.MapNode(fsl.ImageMaths(suffix='_bet',
                                     op_string='-mas'),
                      iterfield=['in_file'],
                      name = 'maskfunc')
psb6351_wf.connect(tshifter, 'out_file', maskfunc, 'in_file')
psb6351_wf.connect(fs_voltransform, 'transformed_file', maskfunc, 'in_file2')

# Smooth each run using SUSAn with the brightness threshold set to 75%
# of the median value for each run and a mask constituting the mean functional
smooth_median = pe.MapNode(fsl.ImageStats(op_string='-k %s -p 50'),
                           iterfield = ['in_file'],
                           name='smooth_median')
smooth_median.plugin_args={'sbatch_args': ('--partition highmem1-sapphirerapids --cpus-per-task=3 --account acc_madlab --qos highmem1'), 'overwrite': True}
psb6351_wf.connect(maskfunc, 'out_file', smooth_median, 'in_file')
psb6351_wf.connect(fs_voltransform, 'transformed_file', smooth_median, 'mask_file')

# Calculate the mean functional
smooth_meanfunc = pe.MapNode(fsl.ImageMaths(op_string='-Tmean',
                                            suffix='_mean'),
                             iterfield=['in_file'],
                             name='smooth_meanfunc')
smooth_meanfunc.plugin_args={'sbatch_args': ('--partition highmem1-sapphirerapids --cpus-per-task=3 --account acc_madlab --qos highmem1'), 'overwrite': True}
psb6351_wf.connect(maskfunc, 'out_file', smooth_meanfunc, 'in_file')

smooth_merge = pe.Node(util.Merge(2, axis='hstack'),
                       name='smooth_merge')
psb6351_wf.connect(smooth_meanfunc, 'out_file', smooth_merge, 'in1')
psb6351_wf.connect(smooth_median, 'out_stat', smooth_merge, 'in2')

# Below is the code for smoothing using the susan algorithm from FSL that
# limits smoothing based on different tissue classes
smooth = pe.MapNode(fsl.SUSAN(),
                    iterfield=['in_file', 'brightness_threshold', 'usans'],
                    name='smooth')
smooth.inputs.fwhm=4.0
smooth.plugin_args={'sbatch_args': ('--partition highmem1-sapphirerapids --cpus-per-task=3 --account acc_madlab --qos highmem1'), 'overwrite': True}
psb6351_wf.connect(maskfunc, 'out_file', smooth, 'in_file')
psb6351_wf.connect(smooth_median, ('out_stat', getbtthresh), smooth, 'brightness_threshold')
psb6351_wf.connect(smooth_merge, ('out', getusans), smooth, 'usans')

# NODE 12: TEMPORAL FILTERING OR SMOOTHING
deconvolve = pe.MapNode(afni.Deconvolve(),
                        iterfield = ['in_files'],
                        name = 'deconvolve')
deconvolve.inputs.legendre = True
deconvolve.inputs.x1D_stop = True
deconvolve.inputs.automask = False
deconvolve.inputs.x1D = 'output.xmat.1D'
deconvolve.inputs.polort = 7
psb6351_wf.connect(smooth, 'smoothed_file', deconvolve, 'in_files')

remlfit = pe.MapNode(afni.Remlfit(),
                     iterfield = ['in_files', 'matrix'],
                     name = 'remlfit')
remlfit.inputs.outputtype = 'NIFTI_GZ'
remlfit.inputs.errts_file = 'func_task_resids.nii.gz'
remlfit.plugin_args={'sbatch_args': ('--partition highmem1-sapphirerapids --cpus-per-task=3 --account acc_madlab --qos highmem1'), 'overwrite': True}
psb6351_wf.connect(smoothed_file, 'smoothed_file', remlfit, 'in_files')
psb6351_wf.connect(deconvolve, 'x1D', remlfit, 'matrix')


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
# The fMRI files in the below connection line have had the following preprocessing steps applied
# 1 - Motion correction (Node #7) to best vol in first 200 of 1st run
# 2 - Slice timing correction (Node #9) using info gleaned from json side cars
# 3 - Skullstripped (Node maskfunc) using the binarized and dilated aparc+aseg from FS inverse
#     transformed to the fMRI image space
# 4 - Spatially smoothed (Node #11ish) using the SUSAN algorithm
# 5 - Temporally filtered (Node #12) using AFNI's DCT approach
# If I use the captured residuals from this last step
# I would not include polorts or a high pass filter at the data analytic stage
# which is what we'll do next
psb6351_wf.connect(remlfit, 'errts_file', datasink, 'resids')
psb6351_wf.connect(getsubs, 'subs', datasink, 'substitutions')

psb6351_wf.config['execution']['use_relative_paths'] = True
psb6351_wf.config['execution']['crashdump_dir'] = '/scratch/madlab/Mattfeld_PSB6351/ATM/crash'
psb6351_wf.run(plugin='SLURM',
               plugin_args={'sbatch_args': ('--partition highmem1-sapphirerapids --account acc_madlab --qos highmem1'),
                            'overwrite':True})
