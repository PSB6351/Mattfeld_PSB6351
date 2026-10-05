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
    t1w = create_key('sub-{subject}/{session}/anat/sub-{subject}_{session}_run-{item}_T1w')
    dmri = create_key('sub-{subject}/{session}/dwi/sub-{subject}_{session}_run-{item}_dwi')
    fmriloc = create_key('sub-{subject}/{session}/func/sub-{subject}_{session}_task-roiloc_run-{item}_bold')
    fmrirevl = create_key('sub-{subject}/{session}/func/sub-{subject}_{session}_task-revl_run-{item}_bold')
    fmriap = create_key('sub-{subject}/{session}/fmap/sub-{subject}_{session}_acq-func_dir-AP_run-{item}_epi')
    fmripa = create_key('sub-{subject}/{session}/fmap/sub-{subject}_{session}_acq-func_dir-PA_run-{item}_epi')
    dmriap = create_key('sub-{subject}/{session}/fmap/sub-{subject}_{session}_acq-dwi_dir-AP_run-{item}_epi')
    dmripa = create_key('sub-{subject}/{session}/fmap/sub-{subject}_{session}_acq-dwi_dir-PA_run-{item}_epi')

    info = {
            t1w : [],
            dmri : [],
            fmriloc : [],
            fmrirevl : [],
            fmriap : [],
            fmripa : [],
            dmriap : [],
            dmripa : []
           }

    for s in seqinfo:
        xdim, ydim, slice_num, timepoints = (s[6], s[7], s[8], s[9])
        if (slice_num == 176) and (timepoints == 1) and ("T1w_MPR_vNav" in s.series_description): #dim 3 = slice num and dim 4 = timepoints
            info[t1w].append(s[2])
        elif (slice_num == 66) and (timepoints == 1) and ("fMRI_DistortionMap_PA" in s.series_description):
            info[fmripa].append(s[2])
        elif (slice_num == 66) and (timepoints == 1) and ("fMRI_DistortionMap_AP" in s.series_description):
            info[fmriap].append(s[2])
        elif (slice_num == 66) and (timepoints == 304) and ("fMRI_REVL_ROI_loc" in s.series_description):
            info[fmriloc].append(s[2])
        elif (slice_num == 66) and (timepoints == 355) and ("fMRI_REVL_Study" in s.series_description):
            info[fmrirevl].append(s[2])
        elif (slice_num == 81) and (timepoints == 1) and ("dMRI_DistortionMap_AP" in s.series_description):
            info[dmriap].append(s[2])
        elif (slice_num == 81) and (timepoints == 1) and ("dMRI_DistortionMap_PA" in s.series_description):
            info[dmripa].append(s[2])
        elif (slice_num == 81) and (timepoints == 103) and ("dMRI_AP_REVL" in s.series_description):
            info[dmri].append(s[2])
        else:
            print("A requested sequence is not found")
            pass
    return info
