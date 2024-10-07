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

<<<<<<< HEAD
    t1w = create_key('sub-{subject}/ses-1/anat/sub-{subject}_ses-1_T1w')
=======
    t1w = create_key('sub-{subject}/ses-1/anat/sub-{subject}_run-{item}_T1w')
    dwi = create_key('sub-{subject}/ses-1/dwi/sub-{subject}_run-{item}_dwi')
    loc1_task = create_key('sub-{subject}/ses-1/func/sub-{subject}_loc_ROI_run-1_bold')
    loc2_task = create_key('sub-{subject}/ses-1/func/sub-{subject}_loc_ROI_run-2_bold')
    study1_task = create_key('sub-{subject}/ses-1/func/sub-{subject}_task-study_run-1_bold')
    study2_task = create_key('sub-{subject}/ses-1/func/sub-{subject}_task-study_run-2_bold')
    study3_task = create_key('sub-{subject}/ses-1/func/sub-{subject}_task-study_run-3_bold')
    study4_task = create_key('sub-{subject}/ses-1/func/sub-{subject}_task-study_run-4_bold')
    task_fmap = create_key('sub-{subject}/ses-1/fmap/sub-{subject}_task-study_run-1_phasediff')
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
>>>>>>> 9f92e9aae013cd55c382ff2655b539f633607352

    #t1w_run1 = create_key('sub-{subject}/ses-1/anat/sub-{subject}_ses-1_run-1_T1w')
    #t1w_run2 = create_key('sub-{subject}/ses-1/anat/sub-{subject}_ses-1_run-2_T1w')

    fmap_pa = create_key('sub-{subject}/ses-1/fmap/sub-{subject}_ses-1_dir-pa_epi')
    fmap_ap = create_key('sub-{subject}/ses-1/fmap/sub-{subject}_ses-1_dir-ap_epi')

    bold_revl_study1 = create_key('sub-{subject}/ses-1/func/sub-{subject}_ses-1_task-study1_bold')
    bold_revl_study2 = create_key('sub-{subject}/ses-1/func/sub-{subject}_ses-1_task-study2_bold')
    bold_revl_study3 = create_key('sub-{subject}/ses-1/func/sub-{subject}_ses-1_task-study3_bold')
    bold_revl_study4 = create_key('sub-{subject}/ses-1/func/sub-{subject}_ses-1_task-study4_bold')

    bold_roi_loc1 = create_key('sub-{subject}/ses-1/func/sub-{subject}_ses-1_task-roiloc1_bold')
    bold_roi_loc2 = create_key('sub-{subject}/ses-1/func/sub-{subject}_ses-1_task-roiloc2_bold')

    dwi_ap = create_key('sub-{subject}/ses-1/dwi/sub-{subject}_ses-1_acq-ap_dwi')
    dwi_pa = create_key('sub-{subject}/ses-1/dwi/sub-{subject}_ses-1_acq-pa_dwi')

    # Setting dictionary
    info = {
        t1w: [],
        #t1w_run1: [],
        #t1w_run2: [],
        t1w: [],
        fmap_pa: [],
        fmap_ap: [],
        bold_revl_study1: [],
        bold_revl_study2: [],
        bold_revl_study3: [],
        bold_revl_study4: [],
        bold_roi_loc1: [],
        bold_roi_loc2: [],
        dwi_ap: [],
        dwi_pa: []
    }

    # Look for unique information to identify unquie scan sequences
    for s in seqinfo:
<<<<<<< HEAD
        if "T1w_MPR_vNav" in s.series_description:
            info[t1w].append(s.series_id)
        #if "4-T1w_MPR_vNav" in s.series_description:
        #    info[t1w_run1].append(s.series_id)
        #elif "5-T1w_MPR_vNav" in s.series_description:
        #    info[t1w_run2].append(s.series_id)

        elif "DistortionMap_PA" in s.series_description:
            info[fmap_pa].append(s.series_id)
        elif "DistortionMap_AP" in s.series_description:
            info[fmap_ap].append(s.series_id)

        elif "REVL_Study_1" in s.series_description:
            info[bold_revl_study1].append(s.series_id)
        elif "REVL_Study_2" in s.series_description:
            info[bold_revl_study2].append(s.series_id)
        elif "REVL_Study_3" in s.series_description:
            info[bold_revl_study3].append(s.series_id)
        elif "REVL_Study_4" in s.series_description:
            info[bold_revl_study4].append(s.series_id)

        elif "ROI_loc_1" in s.series_description:
            info[bold_roi_loc1].append(s.series_id)
        elif "ROI_loc_2" in s.series_description:
            info[bold_roi_loc2].append(s.series_id)

        elif "dMRI_AP" in s.series_description:
            info[dwi_ap].append(s.series_id)
        elif "dMRI_PA" in s.series_description:
            info[dwi_pa].append(s.series_id)

=======
        xdim, ydim, slice_num, timepoints = (s[6], s[7], s[8], s[9])
        if (slice_num == 176) and (timepoints == 1) and ("T1w_MPR_vNav" in s.series_description):
            info[t1w].append(s[2])
        elif (slice_num > 1) and (timepoints == 95) and ("dMRI_AP_REVL" in s[12]):
            info[dwi].append(s[2])
        elif (timepoints == 304) and ("ROI_loc_1" in s[12]):
            info[loc1_task].append(s[2])
        elif (timepoints == 303) and ("ROI_loc_2" in s[12]):
            info[loc2_task].append(s[2])
        elif (timepoints == 355) and ('fMRI_REVL_Study_1' in s[12]):
            info[study1_task].append(s[2])
        elif (timepoints == 351) and ('fMRI_REVL_Study_2' in s[12]):
            info[study2_task].append(s[2])
        elif (timepoints == 350) and ('fMRI_REVL_Study_3' in s[12]):
            info[study3_task].append(s[2])
        elif (timepoints == 345) and ('fMRI_REVL_Study_4' in s[12]):
            info[study4_task].append(s[2])
        elif "dMRI_DistortionMap_AP_dMRI_REVL" in s.series_description:
            info[dwi_fmap].append({"item": s[2], "dir": "AP"})
        elif "dMRI_DistortionMap_PA_dMRI_REVLd" in s.series_description:
            info[dwi_fmap].append({"item": s[2], "dir": "PA"})
        elif "fMRI_DistortionMap_PA" in s.series_description:
            info[task_fmap].append({"item": s[2], "dir": "PA"})
        elif "fMRI_DistortionMap_AP" in s.series_description:
            info[task_fmap].append({"item": s[2], "dir": "AP"})
        else:
            pass
>>>>>>> 9f92e9aae013cd55c382ff2655b539f633607352
    return info

    #for s in seqinfo:
    #    xdim, ydim, slice_num, timepoints = (s[6], s[7], s[8], s[9])
    #    if (slice_num == SOMENUMBER) and (timepoints == 1) and ("NAMEOFSCANTYPE" in s.series_description):
    #        info[keyname(t1w)].append(s[2])
    #    elif (slice_num > SOMEOTHERNUMBER) and (timepoints == SOMETHINGELSE) and ("DIFFERENTNAMEOFSCAN" in s[12]):
    #        info[?].append(s[2])
    #    else:
    #        pass
    #return info
