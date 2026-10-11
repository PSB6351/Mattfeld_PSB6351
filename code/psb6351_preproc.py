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

# class specific info account = acc_psb6351
# class specific info qos = classroom

#SBATCH --account CHANGE FOR CLASS ACCOUNT
#SBATCH --partition highmem1-sapphirerapids <- REMOVE OR CHANGE TO REFLECT CLASS RESOURCES
#SBATCH --qos CHANGE FOR CLASS ACCOUNT
#SBATCH -o /scratch/madlab/Mattfeld_PSB6351/ATM <-CHANGE SO WE DONT WRITE OVER EACH OTHER/crash/preproc_o
#SBATCH -e /scratch/madlab/Mattfeld_PSB6351/ATM <-CHANGE SO WE DONT WRITE OVER EACH OTHER/crash/preproc_e

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
from nipype.interfaces.utility import Function, IdentityInterface
import nibabel as nb
import json
import nipype.interfaces.io as nio
import nipype.pipeline.engine as pe 
import nipype.interfaces.utility as util

# Below I am assigning a list with one string element to the variable named sid
# I do this because I want to iterate over subject ids (aka., sids) and I want 
# to treat 021 as a whole and not as separate parts of the string which is
# also iterable. I know this is a list because of the [] brackets
sids = ['sub-021']

# Below I set up some important directories for getting data and writing
# files that I won't need in the end. I use the os command path.join to 
# combine different string elements into a path strcuture that will work
# across operating systems.  The below is only quasi correct because in the last 
# string element of both thte func_dir and fmap_dir variables I indicate
# directory structures with the '/' string.  This forward slash is only 
# relevant for linux and osx operating systems....windows uses something different '\\'
# I am also using f string formatting to insert the first element of the 
# sids list variable into the string.
base_dir = 'CHANGE ACCORDINGLY TO FIT YOUR ROOT AND PROJECT DIR'
work_dir = '/scratch/madlab/Mattfeld_PSB6351/ATM <- CHANGE HERE SO THAT WE DONT INTERFERE WITH EACH OTHER'
sink_dir = os.path.join(base_dir, 'derivatives/preproc')

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
def slc_time(json_file_list):
    # NOTE: Functions have unique or unshared variables
    #       as well as require unique or unshared libraries/modules
    #       AKA, not global variables or libraries
    import json
    slice_timing_list = [] # Here I define an empty list variable
    for curr_json in json_file_list:
        curr_json_data = open(curr_json) # I need to open the json file
        curr_func_metadata = json.load(curr_json_data) # THen I need to load the json file
        slice_timing_list.append(curr_func_metadata['SliceTiming'])

    return slice_timing_list

# Here I am building a function that eliminates the
# mapnode directory structure and assists in saving
# all of the outputs into a single directory.
# This is a function because it starts with the word def
# and then has the functon name followed by paraentheses.
# The name inside the parentheses is a variable name that represents
# the input to the function.  In this case I'm providing a variable
# called func_files.  I will iterate over the length of the func_files
# variable to append tuples to a list variable called subs that have
# the ways I walsnt to substitute names later in the datasink.  In this
# case I am getting ride of those names so that everything is saved
# in the same directory in the end.
def get_subs(subject_id):
    '''Produces Name Substitutions for Each Contrast'''
    subs = [('_subject_id_%s'%subject_id, '')]
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

def pickfirst(func):
    if isinstance(func, list):
        return func[0]
    else:
        return func

# Here I am building a function that takes in a
# text file that includes the number of outliers
# at each volume and then finds which volume (e.g., index)
# has the minimum number of outliers (e.g., min) 
# searching over the first 201 volumes
# If the index function returns a list because there were
# multiple volumes with the same outlier count, pick the first one
def best_vol(outlier_count, middlebest):
    if middlebest == True:
        best_vol_num = int(np.ceil(len(outlier_count)/2)) #PICKING MIDDLE
    else:
        best_vol_num = outlier_count.index(min(outlier_count[:200]))
        if isinstance(best_vol_num, list):
            best_vol_num = best_vol_num[0]

    return best_vol_num

# Here I am establishing a nipype work flow that I will eventually execute
# Code here become less python specific and more nipype specific.  They share similarites
# but have some unique pecularities to take note.
psb6351_wf = pe.Workflow(name='psb6351_wf') # First I create a workflow...this will serve as the backbone of the pipeline
psb6351_wf.base_dir = work_dir # I deinfe the working directory where I want preliminary files to be written

# NODE 1: This is the node that iterates over the subject ID list
#         It will create a work flow for each subject...in our case just one
subjID_infosource = pe.Node(IdentityInterface(fields=['subject_id']), name = 'subjID_infosource')
subjID_infosource.iterables = ('subject_id', sids)

# NODE 2: The next two chunks of code are necessary for the
#         DataGrabber node.  The info dictionary will grow as
#         you add files to your preprocessing workflow
#         note the relation between the 'subject_id' and the %s
#         in the field_template input below
info = dict(
            fmri_files=[['subject_id', 'subject_id']],
            json_files=[['subject_id', 'subject_id']],
           )

# Create a datasource node to get the files that you are preprocessing
# this will grow as you incoporate more steps into your preprocessing workflow
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
# NOTE: the connection syntax. This is one way of doing it...there are many.
#       You name your upstream node...in this case the subjID_infosource
#       the output of that upstream node = 'subject_id' is named next
#       Then you name the current node that you are connecting to
#       and what input or variable for that node you want to assign the 
#       upstream's output to.
psb6351_wf.connect(subjID_infosource, 'subject_id', datasource, 'subject_id')

# NODE 3: This node is useful for cleaning up some of the weird directory 
#         structure that comes about when saving your data. This is not super
#         important so I'll leave it as is.
# Create a Function node to substitute names of files created during pipeline
# In nipype you create nodes using the pipeline engine that was imported earlier.
# In this case I am sepcifically creating a function node with an input called func_files
# and expects an output (what the function returns) called subs.  The actual function
# which was created above is called get_subs.
# I can assign the input either through a workflow connect syntax or by simplying hardcoding it.
# in this case I hard coded it by saying that .inputs.func_files = func_files
getsubs = pe.Node(Function(input_names=['subject_id'],
                           output_names=['subs'],
                           function=get_subs),
                  name='getsubs')
psb6351_wf.connect(WHAT GOES HERE, 'WHAT GOES HERE?', getsubs, 'subject_id')    

# NODE 4: Here is a node that takes in fMRI data and identifies
#         the number of outliers within each volume within a single 4D MRI scan
#         NOTE - how the pickfirst function is integrated into the connection syntax
# Here I am inputing just the first run functional data
# I want to use afni's 3dToutcount to find the number of 
# outliers at each volume.  I will use this information to
# later select the earliest volume with the least number of outliers
# to serve as the base for the motion correction
id_outliers = pe.Node(afni.OutlierCount(),
                      name = 'id_outliers')
id_outliers.inputs.automask = True
id_outliers.inputs.legendre = True
id_outliers.inputs.polort = 4
id_outliers.inputs.out_file = 'outlier_file'
# NOTE: the connection syntax inserts a function to be applied between the passing
#       of files from one node (e.g., datasource fmri_files) to the next node
#       I am making an assumption as a researcher that I only want to look for
#       outliers for each volume in the first fMRI scan that is collected
#       Do you agree with this approach?  If you don't what would you change?
psb6351_wf.connect(datasource, ('fmri_files', pickfirst), id_outliers, 'in_file')

# NODE 5: This is a function node that take the output from the previous node
#         passes it to the function that is defined above and outputs
#         a specific volume
# Create a Function node to identify the best volume based
# on the number of outliers at each volume. I'm searching
# for the index in the first 201 volumes that has the
# minimum number of outliers and will use the min() function
# I will use the index function to get the best vol.
getbestvol = pe.Node(Function(input_names=['outlier_count', 'middlebest'],
                              output_names=['best_vol_num'],
                              function=best_vol),
                     name='getbestvol')
getbestvol.inputs.middlebest = False
# ADD CONNECTION SYNTAX HERE

# NODE 6: This node is used to extract the specific volume that will serve
#         as the reference for motion correction.
#         How would you modify this node to pick the middle volume?
# Extract the earliest volume with the
# the fewest outliers of the first run as the reference 
extractref = pe.Node(fsl.ExtractROI(t_size=1),
                     name = "extractref")
psb6351_wf.connect(getbestvol, 'best_vol_num', WHAT GOES HERE?, 'WHAT GOES HERE?')
psb6351_wf.connect(datasource, ('fmri_files', pickfirst), extractref, 'in_file')

# NODE 7: This is the node that will perform the motion correction
#         I am using the AFNI tool (I think this is what fMRIPrep uses)
#         What if you wanted to use the FSL tool McFlirt....could you change
#         this node to use that tool?
#         NOTE: I'm not using a MapNode...what is the difference between a Node and a MapNode?
#         Why might you want to use a MapNode in place of a Node?
#         Read the following website for an explanation
#         https://nipype.readthedocs.io/en/0.11.0/users/mapnode_and_iterables.html
# Below is the command that runs AFNI's 3dvolreg command.
# this is the node that performs the motion correction
# I'm iterating over the functional files which I am passing
# functional data from the slice timing correction node before
# I'm using the earliest volume with the least number of outliers
# during the first run as the base file to register to.
# QUESTION - What cost function does AFNI's 3dVolreg use?
volreg = pe.MapNode(afni.Volreg(),
                    iterfield=['in_file'],
                    name = 'volreg')
volreg.inputs.outputtype = 'NIFTI_GZ'
volreg.inputs.zpad = 4
psb6351_wf.connect(extractref, 'roi_file', volreg, 'basefile')
psb6351_wf.connect(datasource, 'fmri_files', volreg, 'in_file')

# NODE 8: This node takes in the list of json files derived from the
#         datagrabber and passes it to a function that builds a list
#         of slice times.  This will be passed to the slice timing correction
#         node as a list along with the motion corrected fMRI files
getslctime = pe.Node(Function(WHAT GOES HERE?,
                              WHAT GOES HERE?,
                              function=WHAT GOES HERE?),
                     name='WHAT GOES HERE?')
# ADD CONNECTION SYNTAX

# NODE 9: This is the node that performs the slice timing correction
#         It requires the motion corrected fMRI files and the list
#         of slice times.  I believe that fMRIPrep also uses this tool for
#         slice timing correction?  
#         How would you change the order of 
#         motion correction and slice timing?
# Below is the command that runs AFNI's 3dTshift command
# this is the node that performs the slice timing correction
# I input the study func files as a list and the slice timing 
# as a list of lists. I'm using a MapNode to iterate over the two.
# this should allow me to parallelize this on the HPC
# QUESTION - What cost function does AFNI's 3dTshift use?

# NOTE: TO DO - BUILD A NODE FOR SLICE TIMING CORRECTION USING
#       AFNI's 3dTshift....is there a comparable tool in FSL? SPM?

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

# NODE FINAL: This is the last node of the workflow. Right now it's number 10
#             But that will icnrease as you add nodes, so I named it Final
#             This saves your output that you want to keep...not peripheral files
#             Take a look at the following webpage to learn more about
#             DataGrabbers and DataSinks
#             https://nipype.readthedocs.io/en/0.11.0/users/grabbing_and_sinking.html
# Below is the node that collects all the data and saves
# the outputs that I am interested in. Here in this node
# I use the substitutions input combined with the earlier
# function to get rid of nesting
datasink = pe.Node(nio.DataSink(), name="datasink")
datasink.inputs.base_directory = sink_dir
psb6351_wf.connect(subjID_infosource, 'subject_id', datasink, 'container')
psb6351_wf.connect(tshifter, 'out_file', datasink, 'sltime_corr')
psb6351_wf.connect(extractref, 'WHAT GOES HERE?', datasink, 'WHAT GOES HERE?')
psb6351_wf.connect(volreg, 'out_file', datasink, 'motion.@corrfile')
psb6351_wf.connect(WHAT GOES HERE?, 'I WANT TO SAVE THE MOTION FILES - WHAT GOES HERE', WHAT GOES HERE?, 'motion.@WHAT GOES HERE?')
psb6351_wf.connect(getsubs, 'subs', datasink, 'substitutions')

# The following two lines set a work directory outside of my 
# local git repo and runs the workflow
psb6351_wf.base_dir = work_dir # I deinfe the working directory where I want preliminary files to be written
psb6351_wf.config['execution']['use_relative_paths'] = True # I assign a execution variable to use relative paths...TRYING TO USE THIS TO FIX A BUG?
psb6351_wf.config['execution']['crashdump_dir'] = '/scratch/madlab/Mattfeld_PSB6351/ATM/crash' <- HOW WOULD THIS NEED TO CHANGE FOR YOUR OWN WORK DIR?
psb6351_wf.run(plugin='SLURM',
               plugin_args={'sbatch_args': ('--account CHANGE HERE FOR CLASS ACCOUNT --qos CHANGE HERE FOR CLASS QOS'),
                            'overwrite':True})
