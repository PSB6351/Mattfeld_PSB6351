from __future__ import annotations
import os

# modify this script 

# heudiconv --files sourcedata/Mattfeld_REVL-000-vCAT-021-S1/scans/*/*/*/*/*.dcm -o raw -f convertall -s 001 -c none --overwrite

# heudiconv --files sourcedata/Mattfeld_REVL-000-vCAT-021-S1/scans/*/*/*/*/*.dcm -o raw -f code/psb6351_heuristic.py -s 001 -ss 01 -c dcm2niix -b


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

    # keyname(e.g.t1w) = create_key('use/this/to/define/sub-{subject}/path/for/file')
    # note you should probably have a key for each scan you want to capture

    t1w = create_key('sub-{subject}/{session}/anat/sub-{subject}_{session}_run-{item:02d}_T1w')
    func_bold = create_key('sub-{subject}/{session}/func/sub-{subject}_{session}_task-{task}_run-{item:02d}_bold')
    dwi = create_key('sub-{subject}/{session}/dwi/sub-{subject}_{session}_run-{item:02d}_dwi')
    fmap_func = create_key('sub-{subject}/{session}/fmap/sub-{subject}_{session}_acq-{acq}_dir-{dir}_run-{item:02d}_epi')
    fmap_dwi = create_key('sub-{subject}/{session}/fmap/sub-{subject}_{session}_acq-{acq}_dir-{dir}_run-{item:02d}_epi')

    info = {t1w: [], func_bold: [], dwi: [], fmap_func: [], fmap_dwi: []}

    for s in seqinfo:
        xdim, ydim, slice_num, timepoints = (s[6], s[7], s[8], s[9])

        if (slice_num == 176) and (timepoints == 1) and ("T1w_MPR_vNav" in s.series_description):
            info[t1w].append(s[2])

        elif (timepoints == 103) and ("dMRI_AP_REVL" in s.protocol_name):
            info[dwi].append({'item': s[2]})

        elif (timepoints == 355) and ("fMRI_REVL_Study" in s.series_description):
            task_num = s.series_description.split('_')[-1]
            info[func_bold].append({'item': s[2], 'task': f'study{task_num}'})

        elif "fMRI_REVL_ROI_loc" in s.series_description:
            run_num = s.series_description.split('_')[-1]
            info[func_bold].append({'item': s[2], 'task': f'loc{run_num}'})

        elif "fMRI_DistortionMap" in s.series_description:
            direction = "AP" if "AP" in s.series_description else "PA"
            info[fmap_func].append({'item': s[2], 'acq': 'func', 'dir': direction})

        elif "dMRI_DistortionMap" in s.series_description:
            direction = "AP" if "AP" in s.series_description else "PA"
            info[fmap_dwi].append({'item': s[2], 'acq': 'dwi', 'dir': direction})

    return info