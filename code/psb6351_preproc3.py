#!/usr/bin/env python


## i've removed most of the assignment notes that were provided in this copy to make it faster to parse lines

## no partition
#SBATCH --account acc_psb6351
#SBATCH --qos classroom
#SBATCH -o /home/eskog001/Mattfeld_PSB6351_eas/code/conversion/pre_proc_o
#SBATCH -e /home/eskog001/Mattfeld_PSB6351_eas/code/conversion/pre_proc_e

import os
from glob import glob

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
# wd prelims
base_dir = '/home/eskog001/Mattfeld_PSB6351_eas'
work_dir = '/home/eskog001/Mattfeld_PSB6351_eas/work'
sink_dir = os.path.join(base_dir, 'derivatives/preproc')

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
# i ran into some issues setting afni path - had to do this manually; ultimately worked
os.environ['PATH'] += ':/home/applications/afni/25.2.07'
os.environ['LD_LIBRARY_PATH'] = os.environ.get('LD_LIBRARY_PATH', '') + ':/home/applications/spack-202506/opt/spack/linux-sapphirerapids/motif-2.3.8-5gv6dfpysx6x42sq5ahtrb5xbvdvitdf/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libxt-1.3.1-io2ikvkn4dc5owt2whr5k7synmsmpyii/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libxft-2.3.8-dj2jatifobe67j534lbw3dnqqfn6olzg/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libxmu-1.2.1-2iyuzberhuplw6zkrfppayebxfwpde6x/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libsm-1.2.6-bfopuwkxowogrmgea22q3jog4m3icmbo/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libice-1.1.2-7dyepgav4bh335ib7miuy3uar2f5zoui/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libpng-1.6.47-hshbhaybhl3dg7pojxgaplot2djkwln2/lib64:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libxext-1.3.6-s2m6nnzuwvo2dvdjqby2lgmvgoebnebe/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libx11-1.8.11-dsqyqveqbcsztzcr5hou4vupdcnverqr/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/libxpm-3.5.17-7tbkl7pprcdkknfzfd6zuvlpxeobuqif/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/mesa-25.0.5-ii4yqltj6qjf7iisbyyve5v4fgbqwcbg/lib:/home/applications/spack-202506/opt/spack/linux-sapphirerapids/mesa-glu-9.0.2-evnqwufx3z5anlf3sdb6uiormskw7qyz/lib:/home/applications/afni/25.2.07/lib'

#-----------------------------------------------------------------------------------------------------------------------
# Fun for extracting slice timing info from fMRI json sidecars
def slc_time(json_file_list):
    import json
    import os
    if isinstance(json_file_list, str):
        json_files = [json_file_list]
    else:
        json_files = json_file_list

    slice_timing_list = []
    for curr_json in json_files:
        if os.path.isdir(curr_json):
            continue
        with open(curr_json, 'r') as f:
            curr_func_metadata = json.load(f)
        slice_timing_list.append(curr_func_metadata['SliceTiming'])
    return slice_timing_list

# Fun for substitutions. Relevant for DataSink
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

# Fun for grabbing aparc+aseg file from fssource node
def get_aparc_aseg(files):
    for name in files:
        if 'aparc+aseg' in name:
            return name
    raise ValueError('aparc+aseg.mgz not found')

# Fun for grabbing the first item in a list
def pickfirst(func):
    if isinstance(func, list):
        return func[0]
    else:
        return func

# Fun for picking the best volume derived from a 
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

#-----------------------------------------------------------------------------------------------------------------------
# NODE 1: Subject iterable, recreate workflow for all subjects in list sids
subjID_infosource = pe.Node(IdentityInterface(fields=['subject_id']), name = 'subjID_infosource')
subjID_infosource.iterables = ('subject_id', sids)

# NODE 2: DataGrabber, currently collecting fMRI and JSON files for run-1
info = dict(
            fmri_files=[['subject_id', 'subject_id']],
            json_files=[['subject_id', 'subject_id']],
           )

datasource = pe.Node(nio.DataGrabber(infields=['subject_id'], outfields=list(info.keys())),
                     name='datasource')
datasource.inputs.template = '*'
datasource.inputs.base_directory = os.path.abspath(base_dir)
datasource.inputs.field_template = dict(
    fmri_files='dset/%s/func/%s_task-study_run-1_bold.nii.gz',
    json_files='dset/%s/func/%s_task-study_run-1_bold.json',
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

# NODE 4: Identify number of outliers in the first fMRI run
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

# NODE 7: Motion correction node - NOTE Applying this before slicetiming
volreg = pe.MapNode(afni.Volreg(),
                    iterfield=['in_file'],
                    name = 'volreg')
volreg.inputs.outputtype = 'NIFTI_GZ'
volreg.inputs.zpad = 4
psb6351_wf.connect(extractref, 'roi_file', volreg, 'basefile')
psb6351_wf.connect(datasource, 'fmri_files', volreg, 'in_file')

# NODE 8: Get list of slice times directly via glob
getslctime = pe.Node(Function(input_names=['json_file_list'],
                              output_names=['slctime_list'],
                              function=slc_time),
                     name='getslctime')
psb6351_wf.connect(datasource, 'json_files', getslctime, 'json_file_list')

# NODE 9: Slicetiming correction node - applied after motion correction
tshifter = pe.MapNode(afni.TShift(),
                      iterfield=['in_file','slice_timing'],
                      name = 'tshifter')
tshifter.inputs.tr = '1.76'
tshifter.inputs.outputtype = 'NIFTI_GZ'
psb6351_wf.connect(volreg, 'out_file', tshifter, 'in_file')
psb6351_wf.connect(getslctime, 'slctime_list', tshifter, 'slice_timing')

# NODE 10: Coregistration of functional to anatomical node using BBRegister
bbregister = pe.Node(fs.BBRegister(init='fsl',
                                   contrast_type='t2',
                                   out_fsl_file=True,
                                   registered_file=True,
                                   subjects_dir=fs_dir),
                     name='bbregister')
psb6351_wf.connect(subjID_infosource, 'subject_id', bbregister, 'subject_id')
psb6351_wf.connect(extractref, 'roi_file', bbregister, 'source_file')

#-----------------------------------------------------------------------------------------------------------------------
# Spatial Smoothing via SUSAN
#-----------------------------------------------------------------------------------------------------------------------
# NODE 11: Spatial smoothing via SUSAN (fsl)
# first we use FreeSurferSource to grab anatomical segments
fssource = pe.Node(nio.FreeSurferSource(), name='fssource' )
fssource.inputs.subjects_dir = fs_dir
psb6351_wf.connect(subjID_infosource, 'subject_id',fssource, 'subject_id')

binarize = pe.Node(fs.Binarize(min=0.5, out_type='nii.gz', binary_file='brain_mask.nii.gz'), name='binarize')
psb6351_wf.connect(fssource, ('aparc_aseg', get_aparc_aseg), binarize, 'in_file')
#transform the mask from t1 to EPI using bbreg
transform_mask = pe.Node(fs.ApplyVolTransform(inverse=True, interp="nearest"), name="transform_mask")
psb6351_wf.connect(bbregister, 'out_reg_file', transform_mask, 'reg_file')
psb6351_wf.connect(binarize, 'binary_file', transform_mask, 'target_file')
psb6351_wf.connect(extractref, 'roi_file', transform_mask, 'source_file')
#mask fEPI dat, then extract median and mean
mask_epi = pe.MapNode(fsl.ImageMaths(op_string='-mas'), iterfield=['in_file'], name='mask_epi')
psb6351_wf.connect(tshifter, 'out_file', mask_epi, 'in_file')
psb6351_wf.connect(transform_mask, 'transformed_file', mask_epi, 'in_file2')
#obain median epi via ImageStats. i ran into a problem using fslmath - this was the only fix
median_epi = pe.MapNode(fsl.ImageStats(op_string='-k %s -p 50'), iterfield=['in_file'], name='median_epi')
psb6351_wf.connect(mask_epi, 'out_file', median_epi, 'in_file')
psb6351_wf.connect(transform_mask, 'transformed_file', median_epi, 'mask_file')
mean_epi = pe.MapNode(fsl.ImageMaths(op_string='-Tmean'), iterfield=['in_file'], name='mean_epi')
psb6351_wf.connect(mask_epi, 'out_file', mean_epi, 'in_file')
# merge both median and mean w/ horiz stack
merge_usans = pe.MapNode(util.Merge(2), iterfield=['in1', 'in2'], name='merge_usans')
psb6351_wf.connect(mean_epi, 'out_file', merge_usans, 'in1')
psb6351_wf.connect(median_epi, 'out_stat', merge_usans, 'in2')

# compute brightness threshold
get_thresh = pe.Node(Function(input_names=['medianvals'], output_names=['thresh'], function=getbtthresh),
                        name='get_thresh')
psb6351_wf.connect(median_epi, 'out_stat', get_thresh, 'medianvals')

# Helper function for USAN
get_usan_struct = pe.Node(Function(input_names=['inlist'], output_names=['usan'], function=getusans),
                             name='get_usan_struct')
psb6351_wf.connect(merge_usans, 'out', get_usan_struct, 'inlist')

# SUSAN SMOOTHING
susan = pe.MapNode(fsl.SUSAN(fwhm=5.0), iterfield=['in_file', 'brightness_threshold', 'usans'], name='susan')
psb6351_wf.connect(mask_epi, 'out_file', susan, 'in_file')
psb6351_wf.connect(get_thresh, 'thresh', susan, 'brightness_threshold')
psb6351_wf.connect(get_usan_struct, 'usan', susan, 'usans')

# NODE 12: Highpass Temporal Filtering
highpass = pe.MapNode(fsl.ImageMaths(suffix='_tempfilt', op_string='-bptf 28.4 -1'), 
                      iterfield=['in_file'], 
                      name='highpass')
psb6351_wf.connect(susan, 'smoothed_file', highpass, 'in_file')

#-----------------------------------------------------------------------------------------------------------------------
# NODE FINAL: Datasink (final connections out)
datasink = pe.Node(nio.DataSink(), name="datasink")
datasink.inputs.base_directory = sink_dir
psb6351_wf.connect(subjID_infosource, 'subject_id', datasink, 'container')
psb6351_wf.connect(extractref, 'roi_file', datasink, 'study_ref')
psb6351_wf.connect(volreg, 'out_file', datasink, 'motion.@corrfile')
psb6351_wf.connect(volreg, 'oned_matrix_save', datasink, 'motion.@matrix')
psb6351_wf.connect(volreg, 'oned_file', datasink, 'motion.@par')
psb6351_wf.connect(tshifter, 'out_file', datasink, 'sltime_corr')
psb6351_wf.connect(bbregister, 'out_reg_file', datasink, 'coreg.@reg_file')
psb6351_wf.connect(bbregister, 'out_fsl_file', datasink, 'coreg.@fsl_mat')
psb6351_wf.connect(bbregister, 'registered_file', datasink, 'coreg.@reg_vol')
psb6351_wf.connect(getsubs, 'subs', datasink, 'substitutions')
psb6351_wf.connect(susan, 'smoothed_file', datasink, 'smoothed') #ADDED FOR SMOOTHING
psb6351_wf.connect(highpass, 'out_file', datasink, 'filtered') #HIGH PASS FILTER

psb6351_wf.config['execution']['use_relative_paths'] = True
psb6351_wf.config['execution']['crashdump_dir'] = '/home/eskog001/Mattfeld_PSB6351_eas/code/conversion'
psb6351_wf.run(plugin='SLURM',
               plugin_args={'sbatch_args': ('--account=acc_psb6351 --qos=classroom --mem=16G'),
                            'overwrite':True})

