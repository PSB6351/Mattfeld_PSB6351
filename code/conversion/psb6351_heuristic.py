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

    T1w_Key = create_key('sub-{subject}/anat/sub-{subject}_T1w')
    fMRI_Key = create_key('sub-{subject}/func/sub-{subject}_task-REVL_bold')
    
    info = {
        T1w_Key: [],
        fMRI_Key: [],
    }
    
    for s in seqinfo:
        xdim, ydim, slice_num, timepoints = (s[6], s[7], s[8], s[9])
        if (slice_num == 176) and (timepoints == 1) and ("T1w" in s.series_description):
            info[T1w_Key].append(s.series_id)
        elif (slice_num > 136) and (timepoints == 135) and ("fMRI" in s.series_description):
            info[fMRI_Key].append(s.series_id)
        
        else:
            pass
    
    return info

    
    
