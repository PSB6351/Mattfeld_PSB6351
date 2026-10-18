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

# list of subject ids
sids = ['sub-021']

# set working, base, and sink directories
base_dir = '/home/cbeac004/Mattfeld_PSB6351'
work_dir = '/home/cbeac004/Mattfeld_PSB6351/preproc_assignment'
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

# NODE 10: Coregistration of functional to anatomical node
#          Using FSL's flirt to register the motion correction reference
#          volume (extractref) to the T1 anatomical scan.
#          Every run was motion corrected to that same volume, so this one
#          transformation applies to all runs.
#          Verify: view the registered EPI (coreg/out_file) on top of the
#          T1 in mango.
#          QUESTIONS:
#          How do you verify that it worked? What would you need to do?
#          - Overlay the registered functional reference volume (flirt
#            output in T1 space) on top of the subject's T1 anatomical scan
#            in a viewer (I used Mango).
#          - Check that the brain lines up with the T1 in all three
#            views: brain outline/edges, ventricles, and anterior/posterior
#            and superior/inferior extent. A failed registration would look
#            shifted, rotated, or scaled relative to the T1.
#          - I had to copy the T1 and the flirt output to my computer (scp)
#            to view them.
#          What would you need to save?
#          - The transformation matrix (out_matrix_file, .mat) so the same
#            func->anat transform can be applied to all runs (they were all
#            motion corrected to the same reference volume) and combined
#            with later transforms.
#          - The registered image (out_file) to visually check the
#            registration.
#          - The T1 used as the reference (already in dset/).
coreg = pe.Node(fsl.FLIRT(), name='coreg')
coreg.inputs.reference = os.path.join(base_dir, 'dset/sub-021/anat/sub-021_run-002_T1w.nii.gz')
coreg.inputs.dof = 6
coreg.inputs.output_type = 'NIFTI_GZ'
psb6351_wf.connect(extractref, 'roi_file', coreg, 'in_file')






# Add a mapnode to spatially blur the data
# save the outputs to the datasink

# Register a source file to fs space and create a brain mask in source space
# The node below creates the Freesurfer source


# Extract aparc+aseg brain mask, binarize, and dilate by 1 voxel

# Transform the binarized aparc+aseg file to the EPI space
# use a nearest neighbor interpolation


# Mask the functional runs with the extracted mask


# Smooth each run using SUSAn with the brightness threshold set to 75%
# of the median value for each run and a mask constituting the mean functional


# Calculate the mean functional


# Below is the code for smoothing using the susan algorithm from FSL that
# limits smoothing based on different tissue classes

# NODE FINAL: DataSink. Modify to save only the files you want at the completion of your workflow
datasink = pe.Node(nio.DataSink(), name="datasink")
datasink.inputs.base_directory = sink_dir
psb6351_wf.connect(subjID_infosource, 'subject_id', datasink, 'container')
psb6351_wf.connect(extractref, 'roi_file', datasink, 'study_ref')
psb6351_wf.connect(volreg, 'out_file', datasink, 'motion.@corrfile')
psb6351_wf.connect(volreg, 'oned_matrix_save', datasink, 'motion.@matrix')
psb6351_wf.connect(volreg, 'oned_file', datasink, 'motion.@par')
psb6351_wf.connect(coreg, 'out_file', datasink, 'coreg.@out_file')
psb6351_wf.connect(coreg, 'out_matrix_file', datasink, 'coreg.@matrix')
psb6351_wf.connect(getsubs, 'subs', datasink, 'substitutions')

psb6351_wf.config['execution']['crashdump_dir'] = '/home/cbeac004/Mattfeld_PSB6351/preproc_assignment/crash'
psb6351_wf.run(plugin='SLURM',
        plugin_args={'sbatch_args': ('--account acc_psb6351 --qos classroom'),                   'overwrite':True})
