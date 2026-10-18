#!/usr/bin/env python

#SBATCH --account acc_gbuzzell
#SBATCH --partition highmem1-sapphirerapids
#SBATCH --qos highmem1
#SBATCH -o /home/cknowlto/scratch/preproc_%j.out
#SBATCH -e /home/cknowlto/scratch/preproc_%j.err

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

# Subjects and important dirs
sids = ['sub-021']
base_dir = '/home/cknowlto/Mattfeld_PSB6351'
work_dir = '/home/cknowlto/scratch'
sink_dir = os.path.join(base_dir, 'derivatives/coregistration')

# Function for extracting slice timing info from fMRI json sidecars
def slc_time(json_file_list):
    import json
    slice_timing_list = [] # Here I define an empty list variable
    for curr_json in json_file_list:
        curr_json_data = open(curr_json) # I need to open the json file
        curr_func_metadata = json.load(curr_json_data) # THen I need to load the json file
        slice_timing_list.append(curr_func_metadata['SliceTiming'])

    return slice_timing_list

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
# searching over all run volumes
# If the index function returns a list because there were
# multiple volumes with the same outlier count, pick the first one

# Modified best volume function to rather select the volume of highest quality 
def best_vol(outlier_files, fmri_files, middlebest):
    counts = [np.loadtxt(f) for f in outlier_files]
    best_run = int(np.argmin([c.min() for c in counts])) # idea here is just to find min omputed from the number of outlier voxels per volume at the LOWEST value to find the "cleanest" volume
    if middlebest == True:
        best_vol_num = int(np.ceil(len(counts[best_run])/2)) #PICKING MIDDLE
    else:
        best_vol_num = int(np.argmin(counts[best_run])) # select volume w/ lowest num of outlier voxels
    return best_vol_num, fmri_files[best_run]

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
            anat_files=[['subject_id', 'subject_id']] # added the t1 scans for coregistration w/ fsl flirt
           )

# Create a datasource node to get the files that you are preprocessing
# this will grow as you incoporate more steps into your preprocessing workflow
datasource = pe.Node(nio.DataGrabber(infields=['subject_id'], outfields=list(info.keys())),
                     name='datasource')
datasource.inputs.template = '*' #since the node is create on the prev line w/ datagrabber now additional parms can be used - this i believe is similar to a wildcard glob formatting which allowas for setting up criteria on how to index certain files in the workflow
datasource.inputs.base_directory = os.path.abspath(base_dir)
datasource.inputs.field_template = dict(
                                        fmri_files='dset2/%s/func/%s*.nii.gz',
                                        json_files='dset2/%s/func/%s_*.json',
                                        anat_files='dset2/%s/anat/%s_run-2_*.nii.gz' # pulling RUN 2 only because run 1 appears to have less granularity and there is less contrast (from doing for f in *T1w.nii.gz; do slicer $f -a ~/${f%.nii.gz}.png; done)
                                       ) #telling workflow to find fmri files in sub dirs in the heudiconv output and then uses sub w/ wildcard to find the nii.gz files and tehn seperately the json side cars in a new var
datasource.inputs.template_args = info
datasource.inputs.sort_filelist = True
datasource.inputs.raise_on_empty = True
# NOTE: the connection syntax. This is one way of doing it...there are many.
#       You name your upstream node...in this case the subjID_infosource ( the node that we just created and then built a workflow with)
#       the output of that upstream node = 'subject_id' is named next
#       Then you name the current node that you are connecting to (like a russian doll of nodes? first doll is subs inside of that is nodes for that sub?)
#       and what input or variable for that node you want to assign the 
#       upstream's output to.
psb6351_wf.connect(subjID_infosource, 'subject_id', datasource, 'subject_id')

# NODE 3: This node is useful for cleaning up some of the weird directory 
#         structure that comes about when saving your data. This is not super
#         important so I'll leave it as is.
# Create a Function node (this is the node that can be upstreamed to sub) to substitute names of files created during pipeline
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
psb6351_wf.connect(subjID_infosource, 'subject_id', getsubs, 'subject_id') #connect func node to upstream sub node

# NODE 4: Here is a node that takes in fMRI data and identifies
#         the number of outliers within each volume within a single 4D MRI scan
#         NOTE - how the pickfirst function is integrated into the connection syntax
# Here I am inputing just the first run functional data
# I want to use afni's 3dToutcount to find the number of 
# outliers at each volume.  I will use this information to
# later select the earliest volume with the least number of outliers
# to serve as the base for the motion correction
id_outliers = pe.MapNode(afni.OutlierCount(), # afni.outlier count wrap for 3dtout used for outlier identification & use mapnode instead to work with iterable field type
                      iterfield=['in_file'], #itereate through all scans
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
# I would make the argument that the first index (i.e., the first scan grabbed) is not necessarily the best for using as the baseline for motion correction. Therefore a better approach would select the least noisy scan and use that for motion correction. To implement this I remove the first addition to the connection portion in the next line and also added the iterate field. I changed the node type to a map node to iterate each run as well
psb6351_wf.connect(datasource, 'fmri_files', id_outliers, 'in_file') # remove pick first

# NODE 5: This is a function node that takes the output from the previous node
#         passes it to the function that is defined above and outputs
#         a specific volume
# I modified the getbestvol func so that I'm searching
# for the volume in all runs that has the
# minimum number of outliers and will use the min() function
# I will use the index function to get the best vol.
getbestvol = pe.Node(Function(input_names=['outlier_files', 'fmri_files', 'middlebest'],
                              output_names=['best_vol_num', 'best_run_file'],
                              function=best_vol,
                              imports=['import numpy as np']), # have to import again since the nodes run seperately
                     name='getbestvol')
getbestvol.inputs.middlebest = False
# ADD CONNECTION SYNTAX HERE
psb6351_wf.connect(id_outliers, 'out_file', getbestvol, 'outlier_files') # run get best vol w/o specifying picking middle to pick volume w/ lowest num of outlier voxels
psb6351_wf.connect(datasource, 'fmri_files', getbestvol, 'fmri_files') # run get best vol w/o specifying picking middle to pick volume w/ lowest num of outlier voxels
# NODE 6: This node is used to extract the specific volume that will serve
#         as the reference for motion correction.
#         How would you modify this node to pick the middle volume?
# I modified how Node 5 pulls the best volume to run based on outlier voxel count. However if you wanted to instead pull the middle volume you can add that parameter since in the function I have an else statement to revert to the computation for pulling the middle volume (total vol / 2).
extractref = pe.Node(fsl.ExtractROI(t_size=1),
                     name = "extractref")
psb6351_wf.connect(getbestvol, 'best_vol_num', extractref, 't_min')
psb6351_wf.connect(getbestvol, 'best_run_file', extractref, 'in_file')

# NODE 7: This is the node that will perform the motion correction
#         I am using the AFNI tool (I think this is what fMRIPrep uses)
#         What if you wanted to use the FSL tool McFlirt....could you change
#         this node to use that tool?
#         Yes, I could change AFNI's Volreg function to FSL's MCFLIRT function in this MapNode and then connect extractref's roi_file to MCFLIRT's ref_file (instead of volreg's basefile).
#         NOTE: I'm not using a MapNode...what is the difference between a Node and a MapNode?
#         I believe this is dated because of the code below does in fact have a map node. The main difference is that in a standard node the iteration occurs once. However, when a node requires multiple runs (for instance over each scan as I implemented above to identify the "best" scan) then a mapnode is better suited since I need to feed it an iterable list.
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
# A weighted least squares function is used in AFNI's 3dVolreg.
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
getslctime = pe.Node(Function(input_names=['json_file_list'],
                            output_names=['slice_timing_list'],
                            function=slc_time),
                    name='getslctime')
# ADD CONNECTION SYNTAX
psb6351_wf.connect(datasource, 'json_files', getslctime, 'json_file_list')
# NODE 9: This is the node that performs the slice timing correction
#         It requires the motion corrected fMRI files and the list
#         of slice times.  I believe that fMRIPrep also uses this tool for
#         slice timing correction?  
#         How would you change the order of 
#         motion correction and slice timing?
# You can change the order by just adjusting the connect function for the node for slice timing correction to connect immediately with the fmri_files and then have the output of that node feed into the connection of the motion correction connect function by change it to the out_file.
# Below is the command that runs AFNI's 3dTshift command
# this is the node that performs the slice timing correction
# I input the study func files as a list and the slice timing 
# as a list of lists. I'm using a MapNode to iterate over the two.
# this should allow me to parallelize this on the HPC
# QUESTION - What cost function does AFNI's 3dTshift use?
# AFNI's 3dTfshift utilizes a fourier transformation at default which does not require a cost function.
# NOTE: TO DO - BUILD A NODE FOR SLICE TIMING CORRECTION USING
#       AFNI's 3dTshift....is there a comparable tool in FSL? SPM?
# FSL by default omits slice-timing correction but can accomplished by using the slicetimer function. SPM also has a bids-compatible approach for slice timing correction available in their GUI interface. Both options allow for custimization within how you process them, such as bottom to top or top to bottom.
# Given that the tr is 1.76 seconds I am going to perform slice timing correction. Although this isn't an obvious case of needing it (sub-second tr for instance)
tshifter = pe.MapNode(afni.TShift(),
                      iterfield=['in_file', 'slice_timing'],
                      name='tshifter')
tshifter.inputs.outputtype = 'NIFTI_GZ'
# save the outputs to the datasink
psb6351_wf.connect(volreg, 'out_file', tshifter, 'in_file')
psb6351_wf.connect(getslctime, 'slice_timing_list', tshifter, 'slice_timing')


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
# Answer: I will need to compare the T1 weighted anatomical to the registered functional volume and see if the sulci/gyri and ventricles line up. I assume what you would want to save from this is an image showing the overlay and that there is a clear line up. In order to accomplish this I used FSL eyes and loaded in the anatomical scan as well as the coregistered functional scan. Then I flickered on and off the view for the registered scan to see how clear brain regions line up (for instance the ventricles should be white on the anatomical scan and when flickering the functional scan on there should be a clear outline in black of the same ventricle). I will show this in class.
#          To complete this assignment, you're going to have to add
#          a node here and modify your DataSink accordingly
#          depending on what tool you use you may need to also
#          modify the recon_all script and add a relevant directory
#          to your node (again...dependent on tool utilized).
skullstrip = pe.Node(fsl.BET(robust=True), name='skullstrip') # FSL flirt reccomends the t1 for coreg to have skull tissue removed with FSL BET
psb6351_wf.connect(datasource, ('anat_files', pickfirst), skullstrip, 'in_file') # update

coreg = pe.Node(fsl.FLIRT(dof=6, cost='corratio'), name='coreg')
psb6351_wf.connect(extractref, 'roi_file', coreg, 'in_file')
psb6351_wf.connect(skullstrip, 'out_file', coreg, 'reference')

# NODE FINAL:
# Below is the node that collects all the data and saves
# the outputs that I am interested in. Here in this node
# I use the substitutions input combined with the earlier
# function to get rid of nesting
datasink = pe.Node(nio.DataSink(), name="datasink")
datasink.inputs.base_directory = sink_dir
psb6351_wf.connect(subjID_infosource, 'subject_id', datasink, 'container')
psb6351_wf.connect(tshifter, 'out_file', datasink, 'sltime_corr')
psb6351_wf.connect(extractref, 'roi_file', datasink, 'motion.@ref')
psb6351_wf.connect(volreg, 'out_file', datasink, 'motion.@corrfile')
psb6351_wf.connect(volreg, 'oned_file', datasink, 'motion.@par')
psb6351_wf.connect(getsubs, 'subs', datasink, 'substitutions')
psb6351_wf.connect(coreg, 'out_matrix_file', datasink, 'coreg.@mat') #transformed matrix
psb6351_wf.connect(coreg, 'out_file', datasink, 'coreg.@registered') # reference volume resampled in t1 space - what I will load into FSL eyes
psb6351_wf.connect(skullstrip, 'out_file', datasink, 'coreg.@anat') #the FSL BET skull tissue removed

# The following two lines set a work directory outside of my 
# local git repo and runs the workflow
psb6351_wf.base_dir = work_dir # I deinfe the working directory where I want preliminary files to be written
psb6351_wf.config['execution']['use_relative_paths'] = True # I assign a execution variable to use relative paths...TRYING TO USE THIS TO FIX A BUG?
psb6351_wf.config['execution']['crashdump_dir'] = '/home/cknowlto/scratch'
psb6351_wf.run(plugin='SLURM',
               plugin_args={'sbatch_args': '--partition highmem1-sapphirerapids --account acc_gbuzzell --qos highmem1',
             'overwrite': True})
