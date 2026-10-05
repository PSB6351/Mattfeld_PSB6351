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
    t1w = create_key('sub-{subject}/{session}/anat/sub-{subject}_run-{item}_T1w')
    fmfunc = create_key('sub-{subject}/{session}/fmap/sub-{subject}_{session}_func_dir-{dir}')
    fmdwi = create_key('sub-{subject}/{session}/fmap/sub-{subject}_{session}_dwi_dir-{dir}')
    roi_loc = create_key('sub-{subject}/{session}/func/sub-{subject}_{session}_task-ROI_loc_run-{item}')
    study = create_key('sub-{subject}/{session}/func/sub-{subject}_{session}_task-study_run-{item}')
    dwi = create_key('sub-{subject}/{session}/dwi/sub-{subject}_{session}_dwi')
    
    # ========== original version below, should also work, replaced with {item} versions above ============
    #roi_loc_r1 = create_key('sub-{subject}/{session}/func/sub-{subject}_{session}_task-ROI_loc_run-1')
	#roi_loc_r2 = create_key('sub-{subject}/{session}/func/sub-{subject}_{session}_task-ROI_loc_run-2')
	#study_r1 = create_key('sub-{subject}/{session}/func/sub-{subject}_{session}_task-study_run-1')
	#study_r2 = create_key('sub-{subject}/{session}/func/sub-{subject}_{session}_task-study_run-2')
	#study_r3 = create_key('sub-{subject}/{session}/func/sub-{subject}_{session}_task-study_run-3')
	#study_r4 = create_key('sub-{subject}/{session}/func/sub-{subject}_{session}_task-study_run-4')

    info = {
            # ADD KEYS FROM ABOVE AND EMPTY LISTS AS VALUES
            # IN THE INFO DICTIONARY...THIS WILL BE USED BELOW
            # TO ASSIGN THE CORRECT DICOMS TO THE RELEVANT SCANS
        t1w : [],
        fmfunc: [],
        roi_loc: [],
        study: [],
        fmdwi: [],
        dwi: [],
        #roi_loc_r1: [],
        #roi_loc_r2: [],
        #study_r1: [],
        #study_r2: [],
        #study_r3: [],
        #study_r4: [],
    }

    for s in seqinfo:
        """
        The namedtuple `s` contains the following fields:

        * total_files_till_now [0]
        * example_dcm_file [1]
        * series_id [2]
        * dcm_dir_name [3]
        * unspecified2 [4] -> series_files
        * unspecified3 [5] -> unspecified
        * dim1 [6]
        * dim2 [7]
        * dim3 [8] (number of slices)
        * dim4 [9] (number of time points)
        * TR [10]
        * TE [11]
        * protocol_name [12]
        * is_motion_corrected [13]
        * is_derived [14]
        * patient_id [15]
        * study_description [16]
        * referring_physician_name [17]
        * series_description [18]
        * image_type [19]
        """

        xdim, ydim, slice_num, timepoints = (s[6], s[7], s[8], s[9])
        
        # t1w
        if (slice_num == 176) and (timepoints == 1) and ("T1w_MPR_vNav" in s.series_description):
            info[t1w].append(s[2])
        # fmri fmap
        elif (slice_num == 66) and (timepoints == 1) and ("fMRI_DistortionMap" in s.series_description):
            direction = "AP" if "AP" in s.series_description else "PA"
            info[fmfunc].append({"item": s[2], "dir": direction})
        # fmap roi loc task
        elif (timepoints == 304) and ("fMRI_REVL_ROI_loc" in s.series_description):
            info[roi_loc].append(s[2])
        # fmri study task
        elif (timepoints == 355) and ("fMRI_REVL_Study" in s.series_description):
            info[study].append(s[2])
        # dmri fmap
        elif (slice_num == 81) and (timepoints == 1) and ("dMRI_DistortionMap" in s.series_description):
            direction = "AP" if "AP" in s.series_description else "PA"
            info[fmdwi].append({"item": s[2], "dir": direction})
        # dmri
        elif (slice_num == 81) and ("dMRI_AP_REVL" in s.series_description):
            info[dwi].append(s[2])

        #elif (timepoints == 304) and ("fMRI_REVL_ROI_loc_1" in s.series_description):
            #info[roi_loc_r1] = [s[2]]
        #elif (timepoints == 304) and ("fMRI_REVL_ROI_loc_2" in s.series_description):
            #info[roi_loc_r2] = [s[2]]
        #elif (timepoints == 355) and ("fMRI_REVL_Study_1" in s.series_description):
            #info[study_r1] = [s[2]]
        #elif (timepoints == 355) and ("fMRI_REVL_Study_2" in s.series_description):
            #info[study_r2] = [s[2]]
        #elif (timepoints == 355) and ("fMRI_REVL_Study_3" in s.series_description):
            #info[study_r3] = [s[2]]
        #elif (timepoints == 355) and ("fMRI_REVL_Study_4" in s.series_description):
            #info[study_r4] = [s[2]]
                        
        else:
            pass
    return info
