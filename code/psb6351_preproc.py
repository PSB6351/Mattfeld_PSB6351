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

# list of subject ids
sids = ['sub-021']

# set working, base, and sink directories
base_dir = '/home/aoste011/Mattfeld_PSB6351'
work_dir = '/home/aoste011/psb6351_work'
sink_dir = os.path.join(base_dir, 'derivatives/preproc')

# FreeSurfer setup for bbregister
# fs_dir is where recon_all writes each subject's folder (e.g., derivatives/freesurfer/sub-021)
fs_dir = os.path.join(base_dir, 'derivatives/freesurfer')
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
# NOTE (my change, kept from last week): the outlier node passes in a text
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
#
# MY ANSWER (tool choice): As my tool choice, I used FreeSurfer's bbregister 
# (boundary-based registration). It needs recon_all to be finished first, so 
# I completed and ran psb6351_run_recon.py first. Then I ran psb6351_preproc.py.
# -source_file: the reference volume from extractref. All runs were motion
#   corrected to this same volume, so one transform applies to every run.
# -contrast_type='t2': BOLD images are T2*-weighted (gray matter brighter
#   than white matter), the opposite of the T1.
# -init='fsl': FSL's flirt gives a rough starting alignment, then
#   bbregister refines it using the white/gray matter boundary.
#
# MY ANSWER (how to verify it worked): There are multiple ways to check if 
# it worked. The way I am checking is by looking at the cost value in the 
# min_cost_file: lower is better, and a high value suggests that the registration 
# probably failed. My mincost was 0.325, which is low and indicates a good 
# registration. This can be visually checked by overlaying the registered functional 
# on the subject's anatomical (brainmask) in Mango/fsleyes and confirming the 
# brain outline, ventricles, and gray matter line up.
#
# MY ANSWER (what to save): There are a few things that should be saved.
# The transformation files should be saved, these are: out_reg_file 
# (.dat, FreeSurfer format) and out_fsl_file (.mat, FSL format), so the 
# functional-to-anatomical transform can be applied in later steps without 
# redoing the registration. Also the registered_file (functional moved into 
# anatomical space) for the visual check, and the min_cost_file as a quality 
# measure.
#
bbreg = pe.Node(fs.BBRegister(contrast_type='t2',
                              init='fsl',
                              out_fsl_file=True,
                              registered_file=True,
                              subjects_dir=fs_dir),
                name='bbreg')
psb6351_wf.connect(subjID_infosource, 'subject_id', bbreg, 'subject_id')
psb6351_wf.connect(extractref, 'roi_file', bbreg, 'source_file')


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
psb6351_wf.connect(bbreg, 'out_reg_file', datasink, 'bbreg.@reg')
psb6351_wf.connect(bbreg, 'out_fsl_file', datasink, 'bbreg.@fslmat')
psb6351_wf.connect(bbreg, 'registered_file', datasink, 'bbreg.@registered')
psb6351_wf.connect(bbreg, 'min_cost_file', datasink, 'bbreg.@mincost')
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
