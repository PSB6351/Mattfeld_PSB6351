#!/usr/bin/env python

# The line at the very top tells the cpu that will be excuting this job
# which python to use and how to find it.
# Without that line this sould just be a simple text file and you would
# specifically need to type on the command line: python name_of_file.py

# The lines below set up important parameters for the slurm scheduling system
# The first line tells the slurm scheduler which partition to send the job to
# The next two lines tells which account to use.
# The last two lines with the -o and -e flags tell where to write out the 
# error and output text files.  These are useful when debugging code.  They
# Are simple text files that cat be viewed with the commands cat or less.
# The directory where these files are written must be created before otherwise
# you won't have access to the output and error text files.

#SBATCH --partition centos7_default-partition
#SBATCH --account acc_psb6351
#SBATCH --qos pq_psb6351
#SBATCH -o /scratch/madlab/Mattfeld_PSB6351/ATM/crash/preproc_o
#SBATCH -e /scratch/madlab/Mattfeld_PSB6351/ATM/crash/preproc_e

# The following commands are specific to python programming.
# Tools that you'll need for your code must be imported.  
# You can import modules directly without renaming them (e.g., import os)
# Or you can import and rename things (e.g., import pandas as pd)
# Or you can import specific features of a module (e.g., from nipype.interfaces.utility import Function)
# It is traditional in python programming to import everything
# you might need at the top of your script.  However, the only rule
# is modules must be imported before they are used.  Also, functions code that begins with def nameoffunc(inputtofunc):
# require importing their own modules

import os
from glob import glob

# Import new things that we'll need
import pandas as pd
import numpy as np
import nipype.interfaces.afni as afni
import nipype.interfaces.fsl as fsl
import nipype.interfaces.freesurfer as fs
from nipype.interfaces.utility import Function
import nibabel as nb
import json
import nipype.interfaces.io as nio
import nipype.pipeline.engine as pe 
import nipype.interfaces.utility as util

# Below I am assigning a list with one string element to the variable named sid
# I do this because I want to iterate over subject ids (aka., sids) and I want 
# to treat 021 as a whole and not as separate parts of the string which is
# also iterable. I know this is a list because of the [] brackets
sids = ['021']

# Below I set up some important directories for getting data and writing
# files that I won't need in the end. I use the os command path.join to 
# combine different string elements into a path strcuture that will work
# across operating systems.  The below is only quasi correct because in the last 
# string element of both thte func_dir and fmap_dir variables I indicate
# directory structures with the '/' string.  This forward slash is only 
# relevant for linux and osx operating systems....windows uses something different '\\'
# I am also using f string formatting to insert the first element of the 
# sids list variable into the string.
base_dir = '/home/data/madlab/Mattfeld_PSB6351/mattfeld_2020'
work_dir = '/scratch/madlab/Mattfeld_PSB6351/ATM'
func_dir = os.path.join(base_dir, f'dset/sub-{sids[0]}/func')
fmap_dir = os.path.join(base_dir, f'dset/sub-{sids[0]}/fmap')
fs_dir = os.path.join(base_dir, 'derivatives', 'freesurfer')

# Get a list of my study task json and nifti converted files
# I am using the glob function from glob that take a string as input
# That string can contain wildcards to grab multiple files that meet 
# the string completion.  I also, use the function sorted to order them
# so that the func_files and fmap_files are in the same order based on
# alphanumeric numbering criteria.  This is important when I get
# specific elements from a .json file for a func file to preprocess.
# Be careful!!!!  glob will return an empty list if your wildcard
# string completion comes up empty rather than crash.  Make sure you 
# have no typos.
# I plan to replace these lines with a nipype datagrabber soon.
func_json = sorted(glob(func_dir + '/*.json'))
func_files = sorted(glob(func_dir + '/*.nii.gz'))
fmap_files = sorted(glob(fmap_dir + '/*func*.nii.gz'))

# Here I am building a function that eliminates the
# mapnode directory structure and assists in saving
# all of the outputs into a single directory.
# This is a function because it starts with the word def
# and then has the functon name followed by paraentheses.
# The name inside the parentheses is a variable name that represents
# the input to the function.  In this case I'm providing a variable
# called func_files.  I will iterate over the length of the func_files
# variable to append tuples to a list variable called subs that have
# the ways I want to substitute names later in the datasink.  In this
# case I am getting ride of those names so that everything is saved
# in the same directory in the end.
def get_subs(func_files):
    '''Produces Name Substitutions for Each Contrast'''
    subs = []
    for curr_run in range(len(func_files)):
        subs.append(('_tshifter%d' %curr_run, ''))
        subs.append(('_volreg%d' %curr_run, ''))
        subs.append(('_smooth%d' %curr_run, ''))
    return subs

def getbtthresh(medianvals):
    """Get the brightness threshold for SUSAN."""
    return [0.75*val for val in medianvals]

def getusans(inlist):
    """Return the usans at the right threshold."""
    return [[tuple([val[0],0.75*val[1]])] for val in inlist]

def get_aparc_aseg(files):
    for name in files:
        if 'aparc+aseg' in name:
            return name
    raise ValueError('aparc+aseg.mgz not found')

# Here I am building a function that takes in a
# text file that includes the number of outliers
# at each volume and then finds which volume (e.g., index)
# has the minimum number of outliers (e.g., min) 
# searching over the first 201 volumes
# If the index function returns a list because there were
# multiple volumes with the same outlier count, pick the first one
def best_vol(outlier_count):
    best_vol_num = outlier_count.index(min(outlier_count[:200]))
    if isinstance(best_vol_num, list):
        best_vol_num = best_vol_num[0]
    return best_vol_num

# Here I am creating a list of lists containing the slice timing for each study run
slice_timing_list = [] # Here I define an empty list variable
for curr_json in func_json: # Here I am iterating over the variable func_json that was deefined above through the sorted glob
    curr_json_data = open(curr_json) # I need to open the json file
    curr_func_metadata = json.load(curr_json_data) # THen I need to load the json file
    slice_timing_list.append(curr_func_metadata['SliceTiming'])

# Here I am establishing a nipype work flow that I will eventually execute
# Code here become less python specific and more nipype specific.  They share similarites
# but have some unique pecularities to take note.
psb6351_wf = pe.Workflow(name='psb6351_wf') # First I create a workflow...this will serve as the backbone of the pipeline
psb6351_wf.base_dir = work_dir + f'/psb6351workdir/sub-{sids[0]}' # I deinfe the working directory where I want preliminary files to be written
psb6351_wf.config['execution']['use_relative_paths'] = True # I assign a execution variable to use relative paths...TRYING TO USE THIS TO FIX A BUG?

# Create a Function node to substitute names of files created during pipeline
# In nipype you create nodes using the pipeline engine that was imported earlier.
# In this case I am sepcifically creating a function node with an input called func_files
# and expects an output (what the function returns) called subs.  The actual function
# which was created above is called get_subs.
# I can assign the input either through a workflow connect syntax or by simplying hardcoding it.
# in this case I hard coded it by saying that .inputs.func_files = func_files
getsubs = pe.Node(Function(input_names=['func_files'],
                           output_names=['subs'],
                           function=get_subs),
                  name='getsubs')
getsubs.inputs.func_files = func_files

# Here I am inputing just the first run functional data
# I want to use afni's 3dToutcount to find the number of 
# outliers at each volume.  I will use this information to
# later select the earliest volume with the least number of outliers
# to serve as the base for the motion correction
id_outliers = pe.Node(afni.OutlierCount(),
                      name = 'id_outliers')
id_outliers.inputs.in_file = func_files[0]
id_outliers.inputs.automask = True
id_outliers.inputs.legendre = True
id_outliers.inputs.polort = 4
id_outliers.inputs.out_file = 'outlier_file'

'''
CURRENTLY CRASHING COMMENTING OUT TO WORK ON LATER
#ATM ONLY: Add an unwarping mapnode here using the field maps
calc_distor_corr = pe.Node(afni.Qwarp(),
                           name = 'calc_distor_corr')
calc_distor_corr.inputs.plusminus = True
calc_distor_corr.inputs.pblur = [0.05, 0.05]
calc_distor_corr.inputs.minpatch = 9
calc_distor_corr.inputs.noweight = True
calc_distor_corr.inputs.outputtype = 'NIFTI_GZ'
calc_distor_corr.inputs.out_file = 'foobar'
calc_distor_corr.inputs.in_file = fmap_files[0]
calc_distor_corr.inputs.base_file = fmap_files[1]

distor_corr = pe.MapNode(afni.NwarpApply(),
                         iterfield=['in_file'],
                         name = 'distor_corr')
distor_corr.inputs.ainterp = 'quintic'
calc_distor_corr.inputs.outputtype = 'NIFTI_GZ'
distor_corr.inputs.in_file = func_files
# The line below is the other way that inputs can be provided to a node
# Rather than hardcoding like above: distor_corr.inputs.ainterp = 'quintic'
# You pass the output from the previous node...in this case calc_distor_corr
# it's output is called 'source_warp' and you pass that to this node distor_corr
# and the relevant input here 'warp'
psb6351_wf.connect(calc_distor_corr, 'source_warp', distor_corr, 'warp')
'''

# Create a Function node to identify the best volume based
# on the number of outliers at each volume. I'm searching
# for the index in the first 201 volumes that has the 
# minimum number of outliers and will use the min() function
# I will use the index function to get the best vol. 
getbestvol = pe.Node(Function(input_names=['outlier_count'],
                              output_names=['best_vol_num'],
                              function=best_vol),
                     name='getbestvol')
psb6351_wf.connect(id_outliers, 'out_file', getbestvol, 'outlier_count')

# Extract the earliest volume with the
# the fewest outliers of the first run as the reference 
extractref = pe.Node(fsl.ExtractROI(t_size=1),
                     name = "extractref")
extractref.inputs.in_file = func_files[0]
#extractref.inputs.t_min = int(np.ceil(nb.load(study_func_files[0]).shape[3]/2)) #PICKING MIDDLE
psb6351_wf.connect(getbestvol, 'best_vol_num', extractref, 't_min')

# Below is the command that runs AFNI's 3dvolreg command.
# this is the node that performs the motion correction
# I'm iterating over the functional files which I am passing
# functional data from the slice timing correction node before
# I'm using the earliest volume with the least number of outliers
# during the first run as the base file to register to.
volreg = pe.MapNode(afni.Volreg(),
                    iterfield=['in_file'],
                    name = 'volreg')
volreg.inputs.outputtype = 'NIFTI_GZ'
volreg.inputs.zpad = 4
volreg.inputs.in_file = func_files
psb6351_wf.connect(extractref, 'roi_file', volreg, 'basefile')

# Below is the command that runs AFNI's 3dTshift command
# this is the node that performs the slice timing correction
# I input the study func files as a list and the slice timing 
# as a list of lists. I'm using a MapNode to iterate over the two.
# this should allow me to parallelize this on the HPC
tshifter = pe.MapNode(afni.TShift(),
                      iterfield=['in_file','slice_timing'],
                      name = 'tshifter')
tshifter.inputs.tr = '1.76'
tshifter.inputs.slice_timing = slice_timing_list
tshifter.inputs.outputtype = 'NIFTI_GZ'
psb6351_wf.connect(volreg, 'out_file', tshifter, 'in_file')

# Calculate the transformation matrix from EPI space to FreeSurfer space
# using the BBRegister command
fs_register = pe.Node(fs.BBRegister(init='fsl'),
                      name ='fs_register')
fs_register.inputs.contrast_type = 't2'
fs_register.inputs.out_fsl_file = True
fs_register.inputs.subject_id = f'sub-{sids[0]}'
fs_register.inputs.subjects_dir = fs_dir
psb6351_wf.connect(extractref, 'roi_file', fs_register, 'source_file')

# Add a mapnode to spatially blur the data
# save the outputs to the datasink

# Register a source file to fs space and create a brain mask in source space
# The node below creates the Freesurfer source
fssource = pe.Node(nio.FreeSurferSource(),
                   name ='fssource')
fssource.inputs.subject_id = f'sub-{sids[0]}'
fssource.inputs.subjects_dir = fs_dir

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
psb6351_wf.connect(maskfunc, 'out_file', smooth_median, 'in_file')
psb6351_wf.connect(fs_voltransform, 'transformed_file', smooth_median, 'mask_file')

# Calculate the mean functional
smooth_meanfunc = pe.MapNode(fsl.ImageMaths(op_string='-Tmean',
                                            suffix='_mean'),
                             iterfield=['in_file'],
                             name='smooth_meanfunc')
psb6351_wf.connect(maskfunc, 'out_file', smooth_meanfunc, 'in_file')

smooth_merge = pe.Node(util.Merge(2, axis='hstack'),
                       name='smooth_merge')
psb6351_wf.connect(smooth_meanfunc, 'out_file', smooth_merge, 'in1')
psb6351_wf.connect(smooth_median, 'out_stat', smooth_merge, 'in2')

# Below is the code for smoothing using the susan algorithm from FSL that
# limits smoothing based on different tissue classes
smooth = pe.MapNode(fsl.SUSAN(),
                    iterfield=['in_file', 'brightness_threshold', 'usans', 'fwhm'],
                    name='smooth')
smooth.inputs.fwhm=[2.0, 4.0, 6.0, 8.0, 10.0, 12.0]
psb6351_wf.connect(maskfunc, 'out_file', smooth, 'in_file')
psb6351_wf.connect(smooth_median, ('out_stat', getbtthresh), smooth, 'brightness_threshold')
psb6351_wf.connect(smooth_merge, ('out', getusans), smooth, 'usans')

# Below is the node that collects all the data and saves
# the outputs that I am interested in. Here in this node
# I use the substitutions input combined with the earlier
# function to get rid of nesting
datasink = pe.Node(nio.DataSink(), name="datasink")
datasink.inputs.base_directory = os.path.join(base_dir, 'derivatives/preproc')
datasink.inputs.container = f'sub-{sids[0]}'
psb6351_wf.connect(tshifter, 'out_file', datasink, 'sltime_corr')
psb6351_wf.connect(extractref, 'roi_file', datasink, 'study_ref')
#psb6351_wf.connect(calc_distor_corr, 'source_warp', datasink, 'distortion')
psb6351_wf.connect(volreg, 'out_file', datasink, 'motion.@corrfile')
psb6351_wf.connect(volreg, 'oned_matrix_save', datasink, 'motion.@matrix')
psb6351_wf.connect(volreg, 'oned_file', datasink, 'motion.@par')
psb6351_wf.connect(fs_register, 'out_reg_file', datasink, 'register.@reg_file')
psb6351_wf.connect(fs_register, 'min_cost_file', datasink, 'register.@reg_cost')
psb6351_wf.connect(fs_register, 'out_fsl_file', datasink, 'register.@reg_fsl_file')
psb6351_wf.connect(smooth, 'smoothed_file', datasink, 'funcsmoothed')
psb6351_wf.connect(getsubs, 'subs', datasink, 'substitutions')

# The following two lines set a work directory outside of my 
# local git repo and runs the workflow
psb6351_wf.run(plugin='SLURM',
               plugin_args={'sbatch_args': ('--partition centos7_default-partition --qos pq_psb6351 --account acc_psb6351'),
                            'overwrite':True})

