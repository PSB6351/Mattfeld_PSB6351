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


# Here I am creating a list of lists containing the slice timing for each study run


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


# Create a Function node to identify the best volume based
# on the number of outliers at each volume. I'm searching
# for the index in the first 201 volumes that has the 
# minimum number of outliers and will use the min() function
# I will use the index function to get the best vol. 


# Extract the earliest volume with the
# the fewest outliers of the first run as the reference 


# Below is the command that runs AFNI's 3dvolreg command.
# this is the node that performs the motion correction
# I'm iterating over the functional files which I am passing
# functional data from the slice timing correction node before
# I'm using the earliest volume with the least number of outliers
# during the first run as the base file to register to.


# Below is the command that runs AFNI's 3dTshift command
# this is the node that performs the slice timing correction
# I input the study func files as a list and the slice timing 
# as a list of lists. I'm using a MapNode to iterate over the two.
# this should allow me to parallelize this on the HPC

# Calculate the transformation matrix from EPI space to FreeSurfer space
# using the BBRegister command


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


# Below is the node that collects all the data and saves
# the outputs that I am interested in. Here in this node
# I use the substitutions input combined with the earlier
# function to get rid of nesting


# The following two lines set a work directory outside of my 
# local git repo and runs the workflow
psb6351_wf.run(plugin='SLURM',
               plugin_args={'sbatch_args': ('--partition centos7_default-partition --qos pq_psb6351 --account acc_psb6351'),
                            'overwrite':True})

