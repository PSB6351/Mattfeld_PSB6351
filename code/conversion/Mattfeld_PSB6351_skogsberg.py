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

    # TO DO
    # ADD KEYS FOR SPECIFIC SCANS AND ESTABLISH DIRECTORY STRUCTURE
    # IN A BIDS COMPATIBLE FORMAT
    t1w = create_key('sub-{subject}/ses-S{SESION}/anat/sub-{subject}_run-{item}_T1w')

    fun_study = create_key('sub-{subject}/func/sub-{subject}_task-study_run-{item}_bold')
    fun_loc = create_key('sub-{subject}/func/sub-{subject}_task-loc_run-{item}_bold')
    map_ap_fun = create_key('sub-{subject}/fmap/sub-{subject}_dir-AP_run-{item}_epi')
    map_pa_fun = create_key('sub-{subject}/fmap/sub-{subject}_dir-PA_run-{item}_epi')
    dwi = create_key('sub-{subject}/dwi/sub-{subject}_dir-AP_run-{item}_dwi')
    map_ap_dwi = create_key('sub-{subject}/fmap/sub-{subject}_acq-dwi_dir-AP_run-{item}_epi')
    map_pa_dwi = create_key('sub-{subject}/fmap/sub-{subject}_acq-dwi_dir-PA_run-{item}_epi')

    info = {
            # ADD KEYS FROM ABOVE AND EMPTY LISTS AS VALUES
            # IN THE INFO DICTIONARY...THIS WILL BE USED BELOW
            # TO ASSIGN THE CORRECT DICOMS TO THE RELEVANT SCANS
            t1w : [],
            fun_study : [],
            fun_loc : [],
            map_ap_fun : [],
            map_pa_fun : [],
            dwi : [],
            map_ap_dwi : [],
            map_pa_dwi : []
           }

    for s in seqinfo:
        xdim, ydim, slice_num, timepoints = (s[6], s[7], s[8], s[9])
        if (slice_num == 176) and (timepoints == 1) and ("T1w_MPR_vNav" in s.series_description):
            info[t1w].append(s[2])
        elif (slice_num == 66) and (timepoints == 355) and ("fMRI_REVL_Study" in s.series_description):
            info[fun_study].append(s[2])
        elif (slice_num == 66) and (timepoints == 304) and ("fMRI_REVL_ROI_loc" in s.series_description):
            info[fun_loc].append(s[2])
        elif (slice_num == 66) and (timepoints == 1) and ("fMRI_DistortionMap" in s.series_description):
                    info[map_ap_fun].append(s[2])
        elif (slice_num == 66) and (timepoints == 1) and ("fMRI_DistortionMap" in s.series_description):
                    info[map_pa_fun].append(s[2])
        elif (slice_num == 81) and (timepoints == 103) and ("dMRI_AP_REVL" in s.series_description):
                    info[dwi].append(s[2])
        elif (slice_num == 81) and (timepoints == 1) and ("dMRI_DistortionMap" in s.series_description):
                    info[dwi].append(s[2])
        elif (slice_num == 81) and (timepoints == 1) and ("dMRI_DistortionMap" in s.series_description):
                    info[dwi].append(s[2])
    
        else:
            pass
    return info
