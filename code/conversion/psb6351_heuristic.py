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

    t1w = create_key('sub-{subject}/ses-1/anat/sub-{subject}_ses-1_T1w')

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