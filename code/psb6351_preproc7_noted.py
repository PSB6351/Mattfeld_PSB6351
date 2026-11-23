#!/usr/bin/env python


## i've removed most of the assignment notes that were provided in this copy to make it faster to parse lines
## localizer runs 1-2 for my final manuscript (v1/v2/ffa roi analysis)

## no partition
## slurm settings for the main job: class account + queue, and where its log files go
#SBATCH --account acc_psb6351
#SBATCH --qos classroom
#SBATCH -o /home/eskog001/Mattfeld_PSB6351_eas/code/conversion/pre_proc_loc_o
#SBATCH -e /home/eskog001/Mattfeld_PSB6351_eas/code/conversion/pre_proc_loc_e



import os #

import numpy as np
import nipype.interfaces.afni as afni
import nipype.interfaces.fsl as fsl
import nipype.interfaces.freesurfer as fs
from nipype.interfaces.utility import Function, IdentityInterface
import nipype.interfaces.io as nio
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.algorithms.rapidart as ra

# list of subject ids
sids = ['sub-021']

# set working, base, and sink directories
# wd prelims
# i'm using new work + sink folders so the localizer outputs don't mix with the study run1 outputs
base_dir = '/home/eskog001/Mattfeld_PSB6351_eas'
work_dir = '/home/eskog001/Mattfeld_PSB6351_eas/work_loc'
sink_dir = os.path.join(base_dir, 'derivatives/preproc_loc')

fs_dir = os.path.join(base_dir, 'derivatives/freesurfer')
os.environ['SUBJECTS_DIR'] = fs_dir

# FreeSurfer prelims
os.environ['FREESURFER_HOME'] = '/home/applications/freesurfer/7.1/freesurfer'
os.environ['PATH'] += ':/home/applications/freesurfer/7.1/freesurfer/bin/'
os.environ['MNI_DIR'] = '/home/applications/freesurfer/7.1/freesurfer/mni'
os.environ['LOCAL_DIR'] = '/home/applications/freesurfer/7.1/freesurfer/local'

# FSL
os.environ['FSLDIR'] = '/home/applications/fsl/6.0.6'
os.environ['FSLOUTPUTTYPE'] = 'NIFTI_GZ'
os.environ['PATH'] += ':/home/applications/fsl/6.0.6/bin:/home/applications/fsl/6.0.6/etc'

# AFNI
# i ran into some issues setting afni path... had to do this manually; ultimately worked
os.environ['PATH'] += ':/home/applications/afni/25.2.07'
os.environ['LD_LIBRARY_PATH'] = os.environ.get('LD_LIBRARY_PATH', '') + ':/home/applications/spack-202506/opt/spack/linux-sapphirerapids/motif-2.3.8-5gv6dfpysx6x42sq5ahtrb5xbvdvitdf/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libxt-1.3.1-io2ikvkn4dc5owt2whr5k7synmsmpyii/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libxft-2.3.8-dj2jatifobe67j534lbw3dnqqfn6olzg/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libxmu-1.2.1-2iyuzberhuplw6zkrfppayebxfwpde6x/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libsm-1.2.6-bfopuwkxowogrmgea22q3jog4m3icmbo/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libice-1.1.2-7dyepgav4bh335ib7miuy3uar2f5zoui/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libpng-1.6.47-hshbhaybhl3dg7pojxgaplot2djkwln2/lib64:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libxext-1.3.6-s2m6nnzuwvo2dvdjqby2lgmvgoebnebe/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libx11-1.8.11-dsqyqveqbcsztzcr5hou4vupdcnverqr/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libxpm-3.5.17-7tbkl7pprcdkknfzfd6zuvlpxeobuqif/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/mesa-25.0.5-ii4yqltj6qjf7iisbyyve5v4fgbqwcbg/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/mesa-glu-9.0.2-evnqwufx3z5anlf3sdb6uiormskw7qyz/lib:/home/applications/afni/25.2.07/lib'

#-----------------------------------------------------------------------------------------------------------------------
# fun for extracting slice timing info from fMRI json sidecars
def slc_time(json_file_list): # input json sidecars for each run
    import json
    import os
    if isinstance(json_file_list, str): # one file given as text -> into a list
        json_files = [json_file_list]
    else:
        json_files = json_file_list # already a list

    slice_timing_list = [] # one list of slice times per run
    for curr_json in json_files: # loop over runs
        if os.path.isdir(curr_json): # skip folders, only read files
            continue
        with open(curr_json, 'r') as f: # open sidecar
            curr_func_metadata = json.load(f) # json -> python dictionary
        slice_timing_list.append(curr_func_metadata['SliceTiming']) # keep the 66 slice times (s)
    return slice_timing_list #into tshifter...

# fun for substitutions. [for DataSink]
def get_subs(subject_id):
    '''Produces Name Substitutions for Each Contrast'''
    subs = [('_subject_id_%s'%subject_id, '')] # rm '_subject_id_sub-021' from output folder names
    return subs

def getbtthresh(medianvals):
    """Get the brightness threshold for SUSAN."""
    return [0.75*val for val in medianvals] #75% of each run's median brain intensity

def getusans(inlist):
    """Return the usans at the right threshold."""
    return [[tuple([val[0],0.75*val[1]])] for val in inlist] #per run: (mean image, 0.75 x median)

# function for grabbing aparc+aseg file from fssource node
def get_aparc_aseg(files): # freesurfersource pushes out aparc files, so this gets them
    for name in files:
        if 'aparc+aseg' in name: # keep the standard cortical + subcortical labels
            return name
    raise ValueError('aparc+aseg.mgz not found')

# fun for grabbing the first item in a list
def pickfirst(func):
    if isinstance(func, list):
        return func[0] # first item = localizer run 1
    else:
        return func # single file passes through

# fun for picking the best volume derived from a list of outlier counts
# fix: id_outliers passes the PATH to the 3dToutcount text file, not the counts
# (before, .index() ran on the path string and picked the first '-' in 'sub-021' -> volume 67 instead of 44)
def best_vol(outlier_count, middlebest):
    import numpy as np
    outlier_count = np.genfromtxt(outlier_count).tolist() # read outlier count for each volume
    if middlebest == True:
        best_vol_num = int(np.ceil(len(outlier_count)/2)) #PICKS MIDDLE
    else:
        best_vol_num = outlier_count.index(min(outlier_count[:200])) # volume with the fewest outliers in the first 200
        if isinstance(best_vol_num, list):
            best_vol_num = best_vol_num[0]

    return best_vol_num # -> extractref (OUT: run1 volume 122)

# workflow and working directory pipeline
psb6351_wf = pe.Workflow(name='psb6351_wf')
psb6351_wf.base_dir = work_dir

#-----------------------------------------------------------------------------------------------------------------------
# NODE 1: subject iterable; workflow for all subjects in list sj ids (subject loop, in this case only 1 sj)
subjID_infosource = pe.Node(IdentityInterface(fields=['subject_id']), name = 'subjID_infosource') # passes the subject id to the other nodes
subjID_infosource.iterables = ('subject_id', sids) # repeat for id in sids

# NODE 2: DataGrabber, collecting fMRI (.nii.gz) and json sidecar (.json) files for localizer runs 1-2
info = dict(
            fmri_files=[['subject_id', 'subject_id']], # fill both %s in the template with the subject id
            json_files=[['subject_id', 'subject_id']], # same for the sidecars
           )

datasource = pe.Node(nio.DataGrabber(infields=['subject_id'], outfields=list(info.keys())), # finds files by pattern
                     name='datasource')
datasource.inputs.template = '*' # default pattern (field_template below overrides it)
datasource.inputs.base_directory = os.path.abspath(base_dir) # search inside the project folder
datasource.inputs.field_template = dict(
    fmri_files='dset/%s/func/%s_task-loc_run-*_bold.nii.gz', # both localizer bold runs
    json_files='dset/%s/func/%s_task-loc_run-*_bold.json', # their sidecars (slice timing)
)
datasource.inputs.template_args = info
datasource.inputs.sort_filelist = True # keep run1 before run2
datasource.inputs.raise_on_empty = True
psb6351_wf.connect(subjID_infosource, 'subject_id', datasource, 'subject_id') # subject id into datagrabber

# NODE 3: substitution function to be used with DataSink
getsubs = pe.Node(Function(input_names=['subject_id'],
                           output_names=['subs'],
                           function=get_subs), # wraps get_subs as a node
                  name='getsubs')
psb6351_wf.connect(subjID_infosource, 'subject_id', getsubs, 'subject_id') # subject id -> getsubs

# NODE 4: identify number of outliers in the first fmri run (localizer run-1)
# NOTE afni.OutlierCount runs afni's 3dToutcount
id_outliers = pe.Node(afni.OutlierCount(), # counts outlier voxels in every volume
                      name = 'id_outliers')
id_outliers.inputs.automask = True # only count voxels inside an auto brain mask
id_outliers.inputs.legendre = True
id_outliers.inputs.polort = 4 # remove a 4th order trend before eval outliers
id_outliers.inputs.out_file = 'outlier_file' # text file: one outlier count per volume
psb6351_wf.connect(datasource, ('fmri_files', pickfirst), id_outliers, 'in_file') # run-1 only (pickfirst)

# NODE 5: Pass outlier text file to this function to pick best volume
getbestvol = pe.Node(Function(input_names=['outlier_count', 'middlebest'],
                              output_names=['best_vol_num'],
                              function=best_vol), # wraps best_vol as a node
                     name='getbestvol')
getbestvol.inputs.middlebest = False # fewest outlier volume, not the middle one
psb6351_wf.connect(id_outliers, 'out_file', getbestvol, 'outlier_count') # outlier counts -> best_vol

# NODE 6: Use FSL tool to isolate/extract best volume
extractref = pe.Node(fsl.ExtractROI(t_size=1), # fslroi: copy out one volume
                     name = "extractref")
psb6351_wf.connect(getbestvol, 'best_vol_num', extractref, 't_min') # volume to copy (best one w least motion noise ??
psb6351_wf.connect(datasource, ('fmri_files', pickfirst), extractref, 'in_file') # from localizer run 1

# NODE 7: Motion correction node ... NOTE applying this before slicetiming
# both localizer runs are aligned to the same reference volume (from run-1)
volreg = pe.MapNode(afni.Volreg(), # 3dvolreg: body motion correction (3 shifts + 3 rotations)
                    iterfield=['in_file'], # mapnode: runs once per localizer run
                    name = 'volreg')
volreg.inputs.outputtype = 'NIFTI_GZ' # save as .nii.gz
volreg.inputs.zpad = 4 # adds temp border of empty slices so edges arent cut off when a vol is rotated
psb6351_wf.connect(extractref, 'roi_file', volreg, 'basefile') # align every volume to the reference
psb6351_wf.connect(datasource, 'fmri_files', volreg, 'in_file') # both raw localizer runs

# NODE 8: get list of slice times from the json sidecars
getslctime = pe.Node(Function(input_names=['json_file_list'],
                              output_names=['slctime_list'],
                              function=slc_time), # wraps slc_time as a node
                     name='getslctime')
psb6351_wf.connect(datasource, 'json_files', getslctime, 'json_file_list') # sidecars -> slice times

# NODE 9: Slicetiming correction node, applied after motion correction
# multiband 3 -> 66 slices collected in 22 groups, the json slice times handle this
tshifter = pe.MapNode(afni.TShift(), # 3dTshift: slice timing correction
                      iterfield=['in_file','slice_timing'], # once per run, each with its own slice times
                      name = 'tshifter') #using tshifter
tshifter.inputs.tr = '1.76' # repetition time (s)
tshifter.inputs.outputtype = 'NIFTI_GZ'
psb6351_wf.connect(volreg, 'out_file', tshifter, 'in_file') # motion corrected data in
psb6351_wf.connect(getslctime, 'slctime_list', tshifter, 'slice_timing') # slice times in

# NODE 10: Coregistration of functional to anatomical node using BBRegister
# from my understanding, fmri images are low res & blurry, while FreeSurfer is sharp @ 1mm and is checking for V1/V2/FFA via anatomical scan
#this creates a map to link the two (only the mapping is computed here, the functional data arent moved)
bbregister = pe.Node(fs.BBRegister(init='fsl',
                                   contrast_type='t2', # gray mat is brighter than white
                                   out_fsl_file=True, #outputs a registration file + fsl version
                                   registered_file=True, # saves the reference resampled into t1 space (used for the slicer qa images)
                                   subjects_dir=fs_dir),
                     name='bbregister')
psb6351_wf.connect(subjID_infosource, 'subject_id', bbregister, 'subject_id')
psb6351_wf.connect(extractref, 'roi_file', bbregister, 'source_file') # ref volume is image registered to t1


#THE FINAL COST WAS ~0.33 (lower = better fit)

# NODE 11: Spatial smoothing via SUSAN (fsl)
# first use FreeSurferSource to grab anatomical segments
fssource = pe.Node(nio.FreeSurferSource(), name='fssource' ) # grabs freesurfer files
fssource.inputs.subjects_dir = fs_dir 
psb6351_wf.connect(subjID_infosource, 'subject_id',fssource, 'subject_id')

binarize = pe.Node(fs.Binarize(min=0.5, out_type='nii.gz', binary_file='brain_mask.nii.gz'), name='binarize')
# ^^^ takes freesurfer labelled scan and labels are conv to 1, everything else 0
psb6351_wf.connect(fssource, ('aparc_aseg', get_aparc_aseg), binarize, 'in_file')
#transform the mask from t1 to EPI using bbreg
transform_mask = pe.Node(fs.ApplyVolTransform(inverse=True, interp="nearest"), name="transform_mask") #moves mask into functional space (reverse bbreg); nearest keeps it 0/1
psb6351_wf.connect(bbregister, 'out_reg_file', transform_mask, 'reg_file') # bbregister mapping
psb6351_wf.connect(binarize, 'binary_file', transform_mask, 'target_file') # t1 mask to move
psb6351_wf.connect(extractref, 'roi_file', transform_mask, 'source_file') #functional reference = output grid
#mask fEPI dat, then extract median and mean
mask_epi = pe.MapNode(fsl.ImageMaths(op_string='-mas'), iterfield=['in_file'], name='mask_epi') # fslmaths -mas: zero everything outside the brain
psb6351_wf.connect(tshifter, 'out_file', mask_epi, 'in_file')
psb6351_wf.connect(transform_mask, 'transformed_file', mask_epi, 'in_file2') # brain mask (functional space)
#obtain median epi via ImageStats. i ran into a problem using fslmath - this was the only fix on my end. have to run fsleyes locally as well
#thinking it's a module issue in the cluster on my zsh
median_epi = pe.MapNode(fsl.ImageStats(op_string='-k %s -p 50'), iterfield=['in_file'], name='median_epi') # fslstats: 50th percentile (median) inside the mask
psb6351_wf.connect(mask_epi, 'out_file', median_epi, 'in_file') # masked epi = the image the median is taken from
psb6351_wf.connect(transform_mask, 'transformed_file', median_epi, 'mask_file') # -k: only voxels inside the brain mask count
mean_epi = pe.MapNode(fsl.ImageMaths(op_string='-Tmean'), iterfield=['in_file'], name='mean_epi') # -Tmean: average image over time, one per localizer run
# WHAT THIS DOES: gives susan the average epi image, so it judges edges from a clean picture rather than each noise filled volume 
psb6351_wf.connect(mask_epi, 'out_file', mean_epi, 'in_file') # masked epi in
# merge both median and mean w/ horiz stack
merge_usans = pe.MapNode(util.Merge(2), iterfield=['in1', 'in2'], name='merge_usans') #pairs [mean image, median] for each run
psb6351_wf.connect(mean_epi, 'out_file', merge_usans, 'in1')
psb6351_wf.connect(median_epi, 'out_stat', merge_usans, 'in2')

# get brightness threshold
get_thresh = pe.Node(Function(input_names=['medianvals'], output_names=['thresh'], function=getbtthresh),
                        name='get_thresh')
psb6351_wf.connect(median_epi, 'out_stat', get_thresh, 'medianvals') # brightness thresh = 75% of median brain intensity

# helper fun for USAN
get_usan_struct = pe.Node(Function(input_names=['inlist'], output_names=['usan'], function=getusans),
                             name='get_usan_struct')
psb6351_wf.connect(merge_usans, 'out', get_usan_struct, 'inlist')

# SUSAN SMOOTHING OUTPUT
# replaces each voxel with weighted average of itself and neighbors (rand noise averages out, real signal stays)
# 3mm = smallest kernel from the smoothness comparison (1.5x the 2mm voxels, ~4.6mm effective fwhm)
# small kernel keeps the v1/v2 border sharper for the roi analysis
susan = pe.MapNode(fsl.SUSAN(fwhm=3.0), iterfield=['in_file', 'brightness_threshold', 'usans'], name='susan') #3mm is 1.5x voxel size, using brightness threshold from before
psb6351_wf.connect(mask_epi, 'out_file', susan, 'in_file') # masked, slice timed data in
psb6351_wf.connect(get_thresh, 'thresh', susan, 'brightness_threshold') # edge (preserved) cutoff
psb6351_wf.connect(get_usan_struct, 'usan', susan, 'usans') # mean image used to find edges

# no highpass filter for the localizer (why below)
#the face/scene cycle is 75s, too close to the ~100s cutoff of -bptf (bandpass temporal filtering [..fslmaths
#slow drift will be removed later in the glm instead (3dDeconvolve -polort A i believe (CHECK THIS))


# NODE 12: RAPIDART outlier timepoints [[each run]]
# motion = framewise displacement (fwd) from the 3dvolreg parameters, frame to frame (use_differences=True); largest movement of 6 points on a brain-sized box
# intensity = global signal z_score inside the brain mask (>3 = outlier)
# 1mm fwd threshold
art_1mm = pe.MapNode(ra.ArtifactDetect(use_differences=[True, False], use_norm=True, # motion = per frame change, intensity = raw values; one combined motion number (norm)
                                       norm_threshold=1.0, # flag if head(global img) moved >1mm since previous vol
                                       zintensity_threshold=3, # flag if whole brain signal is >3 sd from run mean
                                       parameter_source='AFNI', mask_type='file'), # 3dvolreg params & brainmask
                     iterfield=['realigned_files', 'realignment_parameters'],
                     name='art_1mm')
psb6351_wf.connect(volreg, 'out_file', art_1mm, 'realigned_files') # motion corr data (for intensity)
psb6351_wf.connect(volreg, 'oned_file', art_1mm, 'realignment_parameters') # 6 motion numbers per vol (for motion check)
psb6351_wf.connect(transform_mask, 'transformed_file', art_1mm, 'mask_file') # brain mask for whole brain signal

# 0.5mm fwd threshold [[[same settings as above but stricter motion cutoff]]]
# note: its own node, not a clone (cloned mapnode inputs don't update.. same issue i found w extra susan kernel in the older preproc scripts)
art_05mm = pe.MapNode(ra.ArtifactDetect(use_differences=[True, False], use_norm=True,
                                        norm_threshold=0.5, # >0.5mm movement
                                        zintensity_threshold=3,
                                        parameter_source='AFNI',
                                        mask_type='file'),
                      iterfield=['realigned_files', 'realignment_parameters'],
                      name='art_05mm')
psb6351_wf.connect(volreg, 'out_file', art_05mm, 'realigned_files')
psb6351_wf.connect(volreg, 'oned_file', art_05mm, 'realignment_parameters')
psb6351_wf.connect(transform_mask, 'transformed_file', art_05mm, 'mask_file')


# NODE FINAL: Datasink (final connections out)
datasink = pe.Node(nio.DataSink(), name="datasink")
datasink.inputs.base_directory = sink_dir

psb6351_wf.connect(subjID_infosource, 'subject_id', datasink, 'container')
psb6351_wf.connect(extractref, 'roi_file', datasink, 'study_ref') # ref volume
psb6351_wf.connect(volreg, 'out_file', datasink, 'motion.@corrfile')
psb6351_wf.connect(volreg, 'oned_matrix_save', datasink, 'motion.@matrix')
psb6351_wf.connect(volreg, 'oned_file', datasink, 'motion.@par') # 6 motion params
psb6351_wf.connect(tshifter, 'out_file', datasink, 'sltime_corr') # slice timed runs (unsmoothed)
psb6351_wf.connect(bbregister, 'out_reg_file', datasink, 'coreg.@reg_file') # freesurfer format reg
psb6351_wf.connect(bbregister, 'out_fsl_file', datasink, 'coreg.@fsl_mat') # same reg but fsl format
psb6351_wf.connect(bbregister, 'registered_file', datasink, 'coreg.@reg_vol') # ref resampled into t1 space
psb6351_wf.connect(getsubs, 'subs', datasink, 'substitutions') #CLEANING
psb6351_wf.connect(transform_mask, 'transformed_file', datasink, 'mask') # brain mask in functional space
psb6351_wf.connect(susan, 'smoothed_file', datasink, 'smoothed') # 3mm ker
psb6351_wf.connect(art_1mm, 'outlier_files', datasink, 'art_1mm.@outliers') # 1mm: flagged volume numbers (motion + intensity)
psb6351_wf.connect(art_1mm, 'statistic_files', datasink, 'art_1mm.@stats') # counts by type (motion / intensity / both)
psb6351_wf.connect(art_1mm, 'norm_files', datasink, 'art_1mm.@norm') # fwd values, same for both thresh
psb6351_wf.connect(art_1mm, 'plot_files', datasink, 'art_1mm.@plot') # default rapidart plot (intensity + motion)
psb6351_wf.connect(art_05mm, 'outlier_files', datasink, 'art_05mm.@outliers') # 0.5mm: flagged volume numbers
psb6351_wf.connect(art_05mm, 'statistic_files', datasink, 'art_05mm.@stats') # counts by type
psb6351_wf.connect(art_05mm, 'plot_files', datasink, 'art_05mm.@plot') # default rapidart plot

psb6351_wf.config['execution']['use_relative_paths'] = True
psb6351_wf.config['execution']['crashdump_dir'] = '/home/eskog001/Mattfeld_PSB6351_eas/code/conversion'

psb6351_wf.run(plugin='SLURM',
               plugin_args={'sbatch_args': ('--account=acc_psb6351 --qos=classroom --mem=16G'),
                            'overwrite':True})
