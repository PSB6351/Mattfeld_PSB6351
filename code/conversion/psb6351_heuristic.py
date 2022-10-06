import os

def create_key(template, outtype=('nii.gz',), annotation_classes=None):
    if template is None or not template:
        raise ValueError('Template must be a valid format string')
    return template, outtype, annotation_classes

def infotodict(seqinfo):
    """Heuristic evaluator for determining which runs belong where

    allowed template fields - follow python string module:

    item: index within category
    subject: participant id
    seqitem: run number during scanning
    subindex: sub index within group
    session: ses-[sessionID]
    bids_subject_session_dir: BIDS subject/session directory
    bids_subject_session_prefix: BIDS subject/session prefix
    """

    t1w = create_key('sub-{subject}/ses-1/anat/sub-{subject}_run-{item}_T1w')
    dwi = create_key('sub-{subject}/ses-1/dwi/sub-{subject}_run-{item}_dwi')
    loc1_task = create_key('sub-{subject}/ses-1/func/sub-{subject}_loc1_task')
    loc2_task = create_key('sub-{subject}/ses-1/func/sub-{subject}_loc2_task')
    study1_task = create_key('sub-{subject}/ses-1/func/sub-{subject}_task-study_run-1_bold')
    study2_task = create_key('sub-{subject}/ses-1/func/sub-{subject}_task-study_run-2_bold')
    study3_task = create_key('sub-{subject}/ses-1/func/sub-{subject}_tast-study_run-3_bold')
    study4_task = create_key('sub-{subject}/ses-1/func/sub-{subject}_test-study_run-4-bold')
    task_fmap = create_key('sub-{subject}/ses-1/func/sub-{subject}_task_fmap')
    dwi_fmap = create_key('sub-{subject}/ses-1/func/sub-{subject}_dwi_fmap')


    info = {t1w : [],
            dwi : [],
            loc1_task : [],
            study1_task : [],
            task_fmap : [],
            dwi_fmap : []}

    for s in seqinfo:
        xdim, ydim, slice_num, timepoints = (s[6], s[7], s[8], s[9])
        if (slice_num == ) and (timepoints == 1) and ("" in protocol_name):
            info[t1w].append(s[2])
        elif (slice_num > 1) and (timepoints == ) and ("" in protocol_name):
            info[dwi].append(s[2])
        elif (timepoints == 304) and ("fMRI_REVL_ROI_loc_1" in protocol_name):
            info[loc1_task].append(s[2])
        elif (timepoints == 303) and ("fMRI_REVL_ROI_loc_2" in protocol_name):
            info[loc2_task].append(s[2])
        elif (timepoints == 355) and ("fMRI_REVL_Study_1" in protocol_name):
            info[study1_task].append(s[2])
        elif "dMRI_DistortionMap_AP" in protocol_name:
            info[dwi_fmap].append({"item": s[2], "dir": "AP"})
        elif "" in protocol_name:
            info[dwi_fmap].append({"item": s[2], "dir": "PA"})
        elif "" in protocol_name:
            info[task_fmap].append({"item": s[2], "dir": "PA"})
        elif "fMRI_DistortionMap_AP" in protocol_name:
            info[task_fmap].append({"item": s[2], "dir": "AP"})
        else:
            pass
    return info
