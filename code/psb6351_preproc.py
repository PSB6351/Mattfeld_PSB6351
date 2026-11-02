#!/home/data/madlab/envs/psb6351_env/bin/python
# ^ i dont know why but i was having issues w the modules and this seemed to fix it?? 

# class specific info account = acc_psb6351
# class specific info qos = classroom

# CHANGE YOUR SBATCH ACCORDING TO YOUR ACCESS
#SBATCH --account acc_madlab
#SBATCH --partition highmem1-sapphirerapids
#SBATCH --qos highmem1
#SBATCH -o /scratch/madlab/Mattfeld_PSB6351/SF/crash/preproc_o
#SBATCH -e /scratch/madlab/Mattfeld_PSB6351/SF/crash/preproc_e

# ====================
# 1. SWITCH SETTINGS 
# -- I added this becuause I wanted to keep both approaches to
# -- spatial and temporal filtering (easier/harder) and be able
# -- to run either/both (paths/nodes get built and run)!
# ====================

# Spatial Smoothing Paths: gaussian (first/easier) or susan (second/harder)
SMOOTH_METHODS = ['susan'] # final: susan only, put 'gaussian' to rebuilt v1
# Temporal Smoothing Paths: fsl high-pass filter (first/easier) or afni 3dDeconvolve, 3dREMLfit, legendre polynomial, regression (second/harder)
TEMPORAL_METHODS = ['afni_legendre'] # final: afni only, put 'fsl_hpf' to rebuild v1

# Set a spatially smoothed that feeds the temporal input
# -- basically choosing one from smooth methods above
TEMPORAL_INPUT = 'susan'

# Kernel sizes (mm full-width-half-max)
# -- why here? trying to set it now bc same node can be used for
# -- both smoothing paths
FWHM_LIST = [3.0, 6.0, 9.0, 12.0]

# Setting repetition time and high-pass cutoff period in seconds
TR = 1.76 # from json sidecars!
HP_CUTOFF_SEC = 100.0 

# Number of Legendre polynomials for the temporal filtering
# Trying 7 as recommended. Don't fully understand this conceptually
POLORT = 7

# Setting arguments for running here so I can just reference it alter
# Tried setting a memory request but it is lowkey a random number
HPC_ARGS = {'sbatch_args': ('--partition highmem1-sapphirerapids --cpus-per-task=3 --mem=32G '
                            '--account acc_madlab --qos highmem1'),
            'overwrite': True}

# ===================
# 2. IMPORTS & DIRS 
# -- as is!
# ===================
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
os.environ['FSLOUTPUTTYPE'] = 'NIFTI_GZ'
# set working, base, and sink directories
base_dir = '/home/sfrai003/Mattfeld_PSB6351'
work_dir = '/scratch/madlab/Mattfeld_PSB6351/SF'
sink_dir = os.path.join(base_dir, 'derivatives/preproc')
fs_dir = os.path.join(base_dir, 'derivatives/freesurfer')

# ----- Check -----
# -- SUSAN's brain mask uses Freesurfer aparc+aseg.mgz, so recon-all must have run
# -- Check to confirm prior to starting, hoping to avoid a silly crash!
if 'susan' in SMOOTH_METHODS:
    for sid in sids:
        aparc_path = os.path.join(fs_dir, sid, 'mri', 'aparc+aseg.mgz')
        if not os.path.exists(aparc_path):
            raise FileNotFoundError('SUSAN needs %s but it does not exist. '
                                    'Has recon-all finished for %s?' % (aparc_path, sid))


# ==================
# 3. HELPER FXs
# -- mostly as is
# -- see get_subs
# ==================

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
    '''Produces Name Substitutions for Each Contrast
        --> Added one for the fwhm directories too
    '''
    subs = [('_subject_id_%s'%subject_id, ''),
            ('_fwhm_', 'fwhm-')]
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

# --> I think I had an issue with this, as implied by me having
# a different volume than instructor way back in the first few 
# weeks... but I am unsure why if it is the same as original 
def best_vol(outlier_count, middlebest):
    import numpy as np
    if middlebest == True:
        best_vol_num = int(np.ceil(len(outlier_count)/2)) #PICKING MIDDLE
    else:
        best_vol_num = outlier_count.index(min(outlier_count[:200]))
        if isinstance(best_vol_num, list):
            best_vol_num = best_vol_num[0]

    return best_vol_num

# ==========================
# 4. WF & NODES 1-10
# -- mostly as is
# ==========================

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
                                        fmri_files='dset/%s/ses-*/func/%s*.nii.gz',
                                        json_files='dset/%s/ses-*/func/%s_*.json',
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

# NODE 11: SPATIAL SMOOTHING
# You have a couple of options here...
# If you want to smooth isotropically you can use either AFNI's 3dmerge or FSL's fslmath
# For AFNI's implementation within the context of nipype check out the following page:
# https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.afni.utils.html#nipype.interfaces.afni.utils.Merge
# For FSL's implementation within the context of nipype check out hte following page:
# https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.fsl.utils.html#nipype.interfaces.fsl.utils.Smooth
# QUESTIONS TO ANSWER...
# Q1 - What does isotropic mean?
# Q2 - What are the pros and cons of isotropic spatial smoothing?
# AFNI has some cool tools to help control the final smoothness of your data
# Specifically 3dBlurToFWHM, this function will estimate your intrinsic smoothness and iteratively
# spatially blur up until it achieves a targeted smoothness
# Q3 - Why might this be good?  Are there any potential cons?
# If you intend to use AFNI's 3dBlurToFWHM check out hte following page:
# https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.afni.preprocess.html#nipype.interfaces.afni.preprocess.BlurToFWHM
# NOTE: If you elect to use this one be careful on how big you make your
# kernel as this process is iterative and can take some time
# FSL has some cool tools that help ensure that you spatially smooth like voxels
# This is FSL's SUSAN algorithm, this function will use intensities in voxels
# to constrain smoothing to like intensities (smooth only grey matter with grey matter)
# Q4 - Why might his be good? Cons (hint: begins with an 'e' and ends with 'ge' effects)?
#      How might the cons influence Gaussian Random Field Theory?
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

# --> SF THOUGHTS
# -- Visually overlay the registered functional image on the t1 
# -- structural using afni (or fsleyes), evaluate accuracy
# -- save the registration info, which can include the 
# -- transformatino files (like the matrix), coregistered images 
# -- (like the func scans, normalized scans, or refrence images)
# -- regarding SUSAN, the .dat file written is what is needed to move the
# -- t1w brain mask into epi space later!

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

# --> I pre-set this in part 1 att he top using HPC_ARGS, which i will call
# -- using .plugin_args = HPC_ARGS... hopefully it works!

# NODES FOR SPATIAL SMOOTHING GO HERE!!!!

# ===========================
# 5. SPATIAL SMOOTHING
# ===========================

# NODE 11: SPATIAL SMOOTHING

# You have a couple of options here...
# If you want to smooth isotropically you can use either AFNI's 3dmerge or FSL's fslmath
# For AFNI's implementation within the context of nipype check out the following page:
# https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.afni.utils.html#nipype.interfaces.afni.utils.Merge
# For FSL's implementation within the context of nipype check out hte following page:
# https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.fsl.utils.html#nipype.interfaces.fsl.utils.Smooth

# QUESTIONS TO ANSWER...

# Q1 - What does isotropic mean?
# -- Isotropic means equally in all directions (x, y, z). So in this context, it 
# would be smoothing using a uniform spherical kernel, i think.

# Q2 - What are the pros and cons of isotropic spatial smoothing?
# -- Pros: increases SNR, increases clarity and data alignment.
# -- Cons: blurs distinct boundaries, possibly combining signals from different tissues
# -- reduces the spatial resolution of the data

# AFNI has some cool tools to help control the final smoothness of your data
# Specifically 3dBlurToFWHM, this function will estimate your intrinsic smoothness and iteratively
# spatially blur up until it achieves a targeted smoothness
# Q3 - Why might this be good?  Are there any potential cons?
# -- It calculates the itrinsic smoothness of the data first and then only adds the 
# -- smoothing needed to hit specific target fwhm. in the end, this standardizes
# -- smoothing across subjects.
# -- cons: computationally heavy and long time to run?

# If you intend to use AFNI's 3dBlurToFWHM check out hte following page:
# https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.afni.preprocess.html#nipype.interfaces.afni.preprocess.BlurToFWHM
# NOTE: If you elect to use this one be careful on how big you make your
# kernel as this process is iterative and can take some time
# FSL has some cool tools that help ensure that you spatially smooth like voxels
# This is FSL's SUSAN algorithm, this function will use intensities in voxels
# to constrain smoothing to like intensities (smooth only grey matter with grey matter)
# Q4 - Why might his be good? Cons (hint: begins with an 'e' and ends with 'ge' effects)? How might the cons influence Gaussian Random Field Theory?
# -- it would restrict smoothing to voxels with similar intensities, which preserves 
# -- functional and anatomical boundaries. however, it introduces *edge effects* at the sharp transitions between tissue types.
# -- this violates the GRF theory because that relies on the assumption that spatial smoothness is uniform across the image.
# -- basically, if smoothness is not uniform because of these edge effects, the cluster
# -- corrections that are based on GRF are then invalid...

# If you choose an isotropic approach or AFNI's 3dBlurToFWHM you need
# to add just a single node here.

# ------- 5A. SETTING 1 ITERABLE FOR KERNEL SIZE ---------
# -- WHY? -> Confused about how it would work if botht he gaussian and the 
# -- susan node each have their own iterables... could not figure out a way
# -- to be sure that it would be separate and not mix them (like a 3mm gaussian
# -- and a 9mm susan approach in the same datasink). This seems disorganized
# -- but also could have negative impact on process?
# -- Since the 1 node would lead to both approaches seeing the same fwhm value
# -- i think this could work and stay organized... maybe im overcomplicating!
# -- this is where i call that pre-set list!

fwhm_infosource = pe.Node(IdentityInterface(fields=['fwhm']), name='fwhm_infosource')
fwhm_infosource.iterables = ('fwhm', FWHM_LIST)

# -------- 5B. GAUSSIAN SMOOTHING, V1 APPROACH --------------
# -- Updated to account for the fwhm node above
smooth_gauss = pe.MapNode(fsl.Smooth(), 
                        iterfield=['in_file'], 
                        name='smooth_gauss')
smooth_gauss.plugin_args = HPC_ARGS

# --------- 5C. SUSAN SMOOTHING, V2 APPROACH ----------------
# --> SF NOTES
# -- SUSAN averages voxel with neighbors that are close in space and similar in
# -- intensity, so it smooths gray matter with gray and leaves tissue boundaries
# -- alone. It needs:
# --        - brightness threshold: nipype susan docs, above noise/below contrast
# --            of desired edges. see the getbtthresh helper fx (0.75*median)
# --        - usan image: image used to decide the 'similarity' aspect, using 
# --            mean func. see get usans fx (0.75*median)
# -- Basically I need a brain-only mask in EPI space, median brain intensity, &
# -- a mean EPI? ** Check this again **

# If you choose to use the FSL SUSAN approach, you'll need to add the following
# NODE 1 - FreeSurferSource node, define subjects_dir as the project's freesurfer directory
#          and define subject_id as the subject id
fssource = pe.Node(nio.FreeSurferSource(), name='fssource')
fssource.inputs.subjects_dir = fs_dir

# NODE 2 - You will need to make a brain only mask.  I'm going to guide you to use freesurfers aparc+aseg
#          To do this you'll use freesurfer's binarize function
#          binarizing all values in the aparc+aseg file that are greater than 0.5
#          For this node to work connect the fssource node and in the connection syntax
#          imbed the get_aparc_aseg function that is already defined for you above
#          Use this node to also dilate your brian only mask in T1w space by 1 voxel
fs_threshold = pe.Node(fs.Binarize(min=0.5, dilate=1, out_type='nii.gz'),
                        name='fs_threshold')

# NODE 3 - Now you have a brain only mask in T1w space...you need to move this into the
#          EPI space by applying the volume transform from T1w space into EPI space
#          NOTE: This step is best implemented if you used Freesurfer's BBREGISTER for coregistration
#          You have to define where you're going aka 'source_file' and what is moving aka 'target_file'
#          You have to pass the registration matrix file derived from your coregistration node
#          You also have to choose an interpolation...

# Q5 - why is nearest neighbor interpolation correct here? What is nearest neighbor interpolation?
# -- nearest neighbor interpolation resamples an image by assigning each new voxel 
# -- the exact value of the closest original value, without blending. here it would be
# -- correct because of transforming a binary mask. continuous interpolation methods
# -- would probably average out the edges into fractional decimals (partial voluming?), which gets rid of the strict binary aspect.
warp_mask = pe.Node(fs.ApplyVolTransform(inverse=True, interp='nearest'),
                    name='warp_mask')
warp_mask.inputs.subjects_dir = fs_dir

# NODE 4 - Now use the mask that is in EPI space to mask the EPI image by voxels that only cover the brain
#          you can use FSL's fslmaths and the '-mas' flag to work here
# --> Why would this be a MapNode? I am doing it so it does it for each run? 
# -- Kind of confused here... the mask is the same for every run but i still have to
# account for all of them -> MapNode?
mask_epi = pe.MapNode(fsl.ImageMaths(op_string='-mas', suffix='_mask'),
                        iterfield=['in_file'],
                        name='mask_epi')
mask_epi.plugin_args = HPC_ARGS

# NODE 5 - Get the median of your EPI data using FSL's fslmath with the following op_string = '-k %s -p 50'
# --> Would this be one number PER RUN?
# --> Is the %s in op_string the mask_file from above? 
median = pe.MapNode(fsl.ImageStats(op_string='-k %s -p 50'),
                    iterfield=['in_file'],
                    name='median')
median.plugin_args = HPC_ARGS

# NODE 6 - Get the mean of your EPI data using FSL's fslmath with the following op_string = '-Tmean'
meanfunc = pe.MapNode(fsl.ImageMaths(op_string='-Tmean', suffix='_mean'),
                        iterfield=['in_file'],
                        name='meanfunc')
meanfunc.plugin_args = HPC_ARGS

# NODE 7 - Use Nipype's util.Merge function to take in 2 inputs and horizontal stack the (aka., 'hstack')
#          Define your first input as the mean EPI from NODE 6 and your second input as the median EPI from NODE 5
# --> so basically i want something that looks like [meanrun1, medianrun1], etc.
# -- but i am working from list a [meanrun1, meanrun2, ...] and 
# -- list b [medianrun1, medianrun2, ...].
# -- so i use the merge function to change it to what i want!
# -- how does it know to grab things from nodes 5 and 6??? im confused****
# -- > the connect statements, silly
# -- why wouldnt this be a mapnode? 
# -- > i think it is because the merge takes the whole list as input so it's done in one go?
merge_usans = pe.Node(util.Merge(2, axis='hstack'), name='merge_usans')

# NODE 8 - Now you have all you need to implement the SUSAN smooth node
#          Pass a list of variable smoothing kernel FWHM sizes, use a mapnode to iterate over them
#          What else needs to be in your iterfield?
# --> iterfield should include each input that is a list, which i think includes
# -- in_file, brightness_threshold, and usans.
# -- the mapnode is supposed to zip these three things together for each run!
# -- i am not putting fwhm in the iterfield because... it is 1 value (3, 6, 9, 12)
# -- per workflow. this is not an issue because it arrives from the fwhm_infosource
# -- iterable
smooth_susan = pe.MapNode(fsl.SUSAN(),
                            iterfield=['in_file', 'brightness_threshold', 'usans'],
                            name='smooth_susan')
smooth_susan.plugin_args = HPC_ARGS
# --> Defaults from nipype docs: dimension=3, use_median=1, ...?

# ------- 5D. CONNECTIONS RE: SWITCH FOR SPATIAL ----------
if 'gaussian' in SMOOTH_METHODS:
    psb6351_wf.connect(tshifter, 'out_file', smooth_gauss, 'in_file')
    psb6351_wf.connect(fwhm_infosource, 'fwhm', smooth_gauss, 'fwhm')

if 'susan' in SMOOTH_METHODS:
    # 1. Build the mask (t1 -> epi space)
    psb6351_wf.connect(subjID_infosource, 'subject_id', fssource, 'subject_id')
    psb6351_wf.connect(fssource, ('aparc_aseg', get_aparc_aseg), fs_threshold, 'in_file')
    psb6351_wf.connect(extractref, 'roi_file', warp_mask, 'source_file')
    psb6351_wf.connect(fs_threshold, 'binary_file', warp_mask, 'target_file')
    psb6351_wf.connect(fs_register, 'out_reg_file', warp_mask, 'reg_file')
    # 2. Masked epi -> mean epi??
    psb6351_wf.connect(tshifter, 'out_file', mask_epi, 'in_file')
    psb6351_wf.connect(warp_mask, 'transformed_file', mask_epi, 'in_file2')
    # *** what is infile2 *** -> if in_file is image being manipulated... in_file2 is the mask????
    psb6351_wf.connect(mask_epi, 'out_file', meanfunc, 'in_file')
    # 3. Median inside the mask
    psb6351_wf.connect(tshifter, 'out_file', median, 'in_file')
    psb6351_wf.connect(warp_mask, 'transformed_file', median, 'mask_file')
    # 4. (mean, median) pairs
    psb6351_wf.connect(meanfunc, 'out_file', merge_usans, 'in1')
    psb6351_wf.connect(median, 'out_stat', merge_usans, 'in2')
    # 5. SUSAN!
    # -- This one makes very little sense, idk if its right
    psb6351_wf.connect(tshifter, 'out_file', smooth_susan, 'in_file')
    # -- trying to get outstat from median node, pass through getbttresh fx, and put that into brightness_thresh... 'tuple'?
    psb6351_wf.connect(median, ('out_stat', getbtthresh), smooth_susan, 'brightness_threshold')
    psb6351_wf.connect(merge_usans, ('out', getusans), smooth_susan, 'usans')
    psb6351_wf.connect(fwhm_infosource, 'fwhm', smooth_susan, 'fwhm')

# NODE DATASINK - Modify your datasink node to collect the smoothed output files so you can visualize
# --> I will come back to this later...

# ===================================
# 6. TEMPORAL FILTERING, TASK DATA
# ===================================

# NODE 12: TEMPORAL FILTERING OR SMOOTHING
# I want you to add a node here to temporally filter the functional data --> should this be a mapnode or regular node?
# If the functional EPI data are resting state data I want you to implement a
# bandpass filter. If the functional EPI data are task data I want you to implement
# a highpass filter.
# Q6 - why bandpass resting state but only highpass task EPI data?
# -- in task fmri, the bold signal of interest happens at specific frequencies that
# -- are task evoked. a low pass filter may accidentally remove the actual task 
# -- signal. so we may opt for removing the slow scanner drift with high pass 
# -- filtering. 

# ---- SWITCH RULES ----
# -- source of temporal, either susan or gauss spatial approach
if TEMPORAL_INPUT == 'susan':
    temporal_src = smooth_susan
else:
    temporal_src = smooth_gauss

# I want you to utilize either the FSL tools implementing fslmaths, what op_string flag would you need?
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

# ----- 6A. FSL HIGH PASS, V1 -----
# -- defined tr and cutoff all the way at the top
hp_sigma_vols = HP_CUTOFF_SEC / (2.0 * TR) 

tempfilt_fsl = pe.MapNode(fsl.ImageMaths(op_string='-bptf %.4f -1' % hp_sigma_vols,
                                    suffix='_hpf',
                                    out_data_type='float'),
                        iterfield=['in_file'],
                        name='tempfilt_fsl')
tempfilt_fsl.plugin_args = HPC_ARGS

# ------ 6B. REGRESSION BASED DETRENDING, V2 --------
# --> 3DDECONVOLVE & 3DREMLFIT
# -- Models the slow drift as a set of smooth functions (Legendre polynomials)..?
# -- Using 2 AFNI functions:
# --    - 3dDeconvolve : builds the design matrix (polynomial regressors)
# --        x1D_stop = True -> just write the matrix
# --    - 3dREMLfit : grabs matrix, fits it voxel by voxel with temporal auto-
# --        correlation and writes teh RESIDUALS (data - fitted drift)
# --        residuals ARE the de-trended data?
# -- Why MapNode? I think because each run needs its own matrix? and then aslo fit?
deconvolve = pe.MapNode(afni.Deconvolve(),
                iterfield=['in_files'],
                name='deconvolve')
deconvolve.inputs.polort= POLORT
deconvolve.inputs.legendre = True
deconvolve.inputs.x1D = 'detrend.xmat.1D'
deconvolve.inputs.x1D_stop = True
deconvolve.inputs.outputtype = 'NIFTI_GZ'   
deconvolve.inputs.num_stimts = 0
deconvolve.plugin_args = HPC_ARGS

remlfit = pe.MapNode(afni.Remlfit(),
                    iterfield=['in_files', 'matrix'],
                    name='remlfit')
remlfit.inputs.errts_file = 'detrended_errts.nii.gz'
remlfit.inputs.outputtype = 'NIFTI_GZ'
remlfit.inputs.num_threads = 3
remlfit.plugin_args = HPC_ARGS

# --> We should only fit the vixels inside the brain mask, right?
remlfit.inputs.automask = True

# ------ 6C. CONNECTIONS FOR TEMPORAL FILT -----
if 'fsl_hpf' in TEMPORAL_METHODS:
    psb6351_wf.connect(temporal_src, 'smoothed_file', tempfilt_fsl, 'in_file')
if 'afni_legendre' in TEMPORAL_METHODS:
    psb6351_wf.connect(temporal_src, 'smoothed_file', deconvolve, 'in_files')
    psb6351_wf.connect(temporal_src, 'smoothed_file', remlfit, 'in_files')
    psb6351_wf.connect(deconvolve, 'x1D', remlfit, 'matrix')

# =====================
# 7. DATASINKS
# =====================
# -- Sink 1: output that does not depend on kernel size, written 1x -> datasink
# -- Sink 2: output that does depend on kernel size (1 copy per FWHM) -> datasink_fwhm
# -- WHY splitting? -> I am trying to avoid copying the motion/reg files each time

# NODE 12: TEMPORAL FILTERING OR SMOOTHING
# I want you to add a node here to temporally filter the functional data --> should this be a mapnode or regular node?
# If the functional EPI data are resting state data I want you to implement a 
# bandpass filter. If the functional EPI data are task data I want you to implement
# a highpass filter.
# Q6 - why bandpass resting state but only highpass task EPI data?
# I want you to utilize either the FSL tools implementing fslmaths, what op_string flag would you need?
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

psb6351_wf.connect(getsubs, 'subs', datasink, 'substitutions')

if 'susan' in SMOOTH_METHODS:
    # trying a QC approach to make life easier (harder)
    # epi brain mask + mean epi -> overlay to quality check
    # that mask covers brain!
    psb6351_wf.connect(warp_mask, 'transformed_file', datasink, 'susan_prep.@epimask')
    psb6351_wf.connect(meanfunc, 'out_file', datasink, 'susan_prep.@meanfunc')

datasink_fwhm = pe.Node(nio.DataSink(), name="datasink_fwhm")
datasink_fwhm.inputs.base_directory = sink_dir
psb6351_wf.connect(subjID_infosource, 'subject_id', datasink_fwhm, 'container')
psb6351_wf.connect(getsubs, 'subs', datasink_fwhm, 'substitutions')

# ADD datasink connections to save spatially smoothed and temporally filtered data
# if you implemented more than one method for diadatic purposes...save accordingly
if 'gaussian' in SMOOTH_METHODS:
    psb6351_wf.connect(smooth_gauss, 'smoothed_file', datasink_fwhm, 'smooth_gaussian.@smoothed')
if 'susan' in SMOOTH_METHODS:
    psb6351_wf.connect(smooth_susan, 'smoothed_file', datasink_fwhm, 'smooth_susan.@smoothed')
if 'fsl_hpf' in TEMPORAL_METHODS:
    psb6351_wf.connect(tempfilt_fsl, 'out_file', datasink_fwhm, 'tempfilt_fsl_%s.@hpf' % TEMPORAL_INPUT)
if 'afni_legendre' in TEMPORAL_METHODS:
    psb6351_wf.connect(remlfit, 'errts_file', datasink_fwhm, 'tempfilt_afni_%s.@errts' % TEMPORAL_INPUT)
    psb6351_wf.connect(deconvolve, 'x1D', datasink_fwhm, 'tempfilt_afni_%s.@x1D' % TEMPORAL_INPUT)



# =======================
# 8. RUN
# =======================

psb6351_wf.config['execution']['use_relative_paths'] = True
psb6351_wf.config['execution']['crashdump_dir'] = '/scratch/madlab/Mattfeld_PSB6351/SF/crash'
psb6351_wf.run(plugin='SLURM',
               plugin_args={'sbatch_args': ('--partition highmem1-sapphirerapids --account acc_madlab --qos highmem1'),
                            'overwrite':True})
