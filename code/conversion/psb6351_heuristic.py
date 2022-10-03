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
    loc1_task = create_key('sub-{subject}/ses-1/func/sub-{subject}_loc_ROI_run-1_bold')
    loc2_task = create_key('sub-{subject}/ses-1/func/sub-{subject}_loc_ROI_run-1_bold')
    study1_task = create_key('sub-{subject}/ses-1/func/sub-{subject}_task-study_run-1_bold')
    study2_task = create_key('sub-{subject}/ses-1/func/sub-{subject}_task-study_run-2_bold')
    study3_task = create_key('sub-{subject}/ses-1/func/sub-{subject}_task-study_run-3_bold')
    study4_task = create_key('sub-{subject}/ses-1/func/sub-{subject}_task-study_run-4_bold')
    task_fmap = create_key('sub-{subject}/ses-1/fmap/sub-{subject}_task-study_run-1_fieldmap')
    dwi_fmap = create_key('sub-{subject}/ses-1/fmap/sub-{subject}_task-study_run-1_b0')

    info = {t1w : [],
            dwi : [],
            loc1_task : [],
            loc2_task : [],
            study1_task : [],
            study2_task : [],
            study3_task : [],
            study4_task : [],
            task_fmap : [],
            dwi_fmap : []}

    for s in seqinfo:
        xdim, ydim, slice_num, timepoints = (s[6], s[7], s[8], s[9])
        if (slice_num == 176) and (timepoints == 1) and ("T1w_MPR_vNav" in s.series_description):
            info[t1w].append(s[2])
        elif (slice_num > 1) and (timepoints == 95) and ("dMRI_AP_REVL" in s[12]):
            info[dwi].append(s[2])
        elif (timepoints == 304) and ("ROI_loc_1" in s[12]):
            info[loc1_task].append(s[2])
        elif (timepoints == 303) and ("ROI_loc_2" in s[12]):
            info[loc2_task].append(s[2])
        elif (timepoints == 355) and ('fMRI_REVL_Study1' in s[12]):
            info[study1_task].append(s[2])
        elif (timepoints == 351) and ('fMRI_REVL_Study2' in s[12]):
            info[study2_task].append(s[2])
        elif (timepoints == 350) and ('fMRI_REVL_Study3' in s[12]):
            info[study3_task].append(s[2])
        elif (timepoints == 345) and ('fMRI_REVL_Study4' in s[12]):
            info[study4_task].append(s[2])
        elif "dMRI_DistortionMap_AP" in s.series_description:
            info[dwi_fmap].append({"item": s[2], "dir": "AP"})
        elif "dMRI_DistortianMap_PA" in s.series_description:
            info[dwi_fmap].append({"item": s[2], "dir": "PA"})
        elif "fMRI_DistortianMap_PA" in s.series_description:
            info[task_fmap].append({"item": s[2], "dir": "PA"})
        elif "fMRI_DistortionMap_AP" in s.series_description:
            info[task_fmap].append({"item": s[2], "dir": "AP"})
        else:
            pass
    return info
