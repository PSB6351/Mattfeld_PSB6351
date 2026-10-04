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

    # KEYS FOR SPECIFIC SCANS AND DIRECTORY STRUCTURE IN A BIDS COMPATIBLE FORMAT
    t1w = create_key('sub-{subject}/anat/sub-{subject}_T1w')
    fmap_func_ap = create_key('sub-{subject}/fmap/sub-{subject}_acq-func_dir-AP_epi')
    fmap_func_pa = create_key('sub-{subject}/fmap/sub-{subject}_acq-func_dir-PA_epi')
    func_loc = create_key('sub-{subject}/func/sub-{subject}_task-loc_run-{item:02d}_bold')
    func_study = create_key('sub-{subject}/func/sub-{subject}_task-study_run-{item:02d}_bold')
    fmap_dwi_ap = create_key('sub-{subject}/fmap/sub-{subject}_acq-dwi_dir-AP_epi')
    fmap_dwi_pa = create_key('sub-{subject}/fmap/sub-{subject}_acq-dwi_dir-PA_epi')
    dwi = create_key('sub-{subject}/dwi/sub-{subject}_dir-AP_dwi')

    info = {
            t1w : [],
            fmap_func_ap : [],
            fmap_func_pa : [],
            func_loc : [],
            func_study : [],
            fmap_dwi_ap : [],
            fmap_dwi_pa : [],
            dwi : [],
            }

    for s in seqinfo:
        if s.is_derived or s.is_motion_corrected:
            continue
        xdim, ydim, slice_num, timepoints = (s[6], s[7], s[8], s[9])
        if (slice_num == 176) and (timepoints == 1) and ("T1w_MPR_vNav" in s.series_description) and ('NORM' in s.image_type):
            info[t1w].append(s[2])
        elif (xdim == 100) and (timepoints == 1) and ("fMRI_DistortionMap_AP" in s.series_description):
            info[fmap_func_ap].append(s[2])
        elif (xdim == 100) and (timepoints == 1) and ("fMRI_DistortionMap_PA" in s.series_description):
            info[fmap_func_pa].append(s[2])
        elif (xdim == 100) and (timepoints == 304) and ("fMRI_REVL_ROI_loc" in s.series_description):
            info[func_loc].append(s[2])
        elif (xdim == 100) and (timepoints == 355) and ("fMRI_REVL_Study" in s.series_description):
            info[func_study].append(s[2])
        elif (xdim == 140) and (timepoints == 1) and ("dMRI_DistortionMap_AP" in s.series_description):
            info[fmap_dwi_ap].append(s[2])
        elif (xdim == 140) and (timepoints == 1) and ("dMRI_DistortionMap_PA" in s.series_description):
            info[fmap_dwi_pa].append(s[2])
        elif (xdim == 140) and (timepoints == 103) and ("dMRI_AP_REVL" in s.series_description):
            info[dwi].append(s[2])
        else:
            pass
    return info
