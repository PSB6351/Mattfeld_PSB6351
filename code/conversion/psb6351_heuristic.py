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

    t1w = create_key("sub-{subject}/anat/sub-{subject}_run-{item:01d}_T1w")
    bold_s1 = create_key("sub-{subject}/func/sub-{subject}_run-{item:01d}-task-bold")
    bold_s2 = create_key("sub-{subject}/func/sub-{subject}_run-{item:01d}-task-bold")
    bold_s3 = create_key("sub-{subject}/func/sub-{subject}_run-{item:01d}-task-bold")
    bold_s4 = create_key("sub-{subject}/func/sub-{subject}_run-{item:01d}-task-bold")
    bold_loc1 = create_key("sub-{subject}/func/sub-{subject}_run-{item:01d}_loc_bold")
    bold_loc2 = create_key("sub-{subject}/func/sub-{subject}_run-{item:01d}_loc_bold")
    bold_fmap_ap = create_key("sub-{subject}/fmap/sub-{subject}_run-{item:01d}_dir_AP_bold")
    bold_fmap_pa = create_key("sub-{subject}/fmap/sub-{subject}_run-{item:01d}_dir_PA_bold")
    dwi = create_key("sub-{subject}/dwi/sub-{subject}_run-{item:01d}_dwi")
    dwi_fmap_ap = create_key("sub-{subject}/fmap/sub-{subject}_run-{item:01d}_dir_AP_dwi")
    dwi_fmap_pa = create_key("sub-{subject}/fmap/sub-{subject}_run-{item:01d}_dir_PA_dwi")
    # note you should probably have a key for each scan you want to capture

    info = {
            t1w : [],
            bold_s1: [],
            bold_s2: [],
            bold_s3: [],
            bold_s4: [],
            bold_loc1: [],
            bold_loc2: [],
            bold_fmap_ap: [],
            bold_fmap_pa: [],
            dwi: [],
            dwi_fmap_ap: [],
            dwi_fmap_pa: [],
           }

    for s in seqinfo:
        xdim, ydim, slice_num, vol_num, TR = (s[6], s[7], s[8], s[9], s[10])
        if (slice_num == 66) and ("fMRI" in s.series_description): # selecting all bold fmri scans for each study separately
            if (vol_num == 355):
                if ("Study_1" in s.series_description):
                    info[bold_s1].append(s[2])
                elif ("Study_2" in s.series_description):
                    info[bold_s2].append(s[2])
                elif ("Study_3" in s.series_description):
                    info[bold_s3].append(s[2])
                elif ("Study_4" in s.series_description):
                    info[bold_s4].append(s[2])
            elif (vol_num == 304): # I'm not sure we need both fmri localizer scans,
                                # I don't know what was the difference between 1st and 2nd scans
                if ("ROI_loc_1" in s.series_description):
                    info[bold_loc1].append(s[2])
                elif ("ROI_loc_2" in s.series_description):
                    info[bold_loc2].append(s[2])
            elif (vol_num == 1): # selecting bold fmaps here because all fMRI scans are in this loop
                # I believe that for distortion maps we need both AP and PA 
                # to be able to correct for field distortions in both directions
                if ("AP" in s.series_description):
                    info[bold_fmap_ap].append(s[2])
                elif ("PA" in s.series_description):
                    info[bold_fmap_pa].append(s[2])
        elif (TR == 2.5) and ("T1w" in s.series_description): # selecting t1w without setter scans 
                                                # I believe we don't need setter scans for the analysis and 
                                                # I've noticed they have very short TR based on which I throw them out

            if s.total_files_till_now == 532: # the remaining two 3 t1 scans looked the same to me (I opened them in dicom imaging software
                                            # although one just looked brighter than other
                                            # I don't really know which one I shall pick so I chose the one with more available files
                info[t1w].append(s[2])
        elif ("DistortionMap" in s.series_description): # dwi fmaps
            if ("dMRI" in s.series_description):
                if ("AP" in s.series_description):
                    info[dwi_fmap_ap].append(s[2])
                elif ("PA" in s.series_description):
                    info[dwi_fmap_pa].append(s[2])
        elif (TR == 4.2) and ("dMRI" in s.series_description):
            info[dwi].append(s[2])
        else:
            pass
    return info
