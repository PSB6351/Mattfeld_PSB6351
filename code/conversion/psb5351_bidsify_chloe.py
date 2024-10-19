from __future__ import annotations

import os


# run command in the terminal w modified paths:
# first time running heudiconv:
# heudiconv --files sourcedata/001/*/resources/DICOM/files/*.dcm -o raw -f convertall -s 001 -ss 01 -c none --overwrite
# once modified heuristics file, convert to bids formatting:
# heudiconv --files sourcedata/001/*/resources/DICOM/files/*.dcm -o raw -f code/psb6351_heuristic.py -s 001 -ss 01 -c dcm2niix -b


def create_key(template, outtype=("nii.gz",), annotation_classes=None):
    if template is None or not template:
        raise ValueError("Template must be a valid format string")
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
    # structural t1w
    t1w = create_key(
        "sub-{subject}/{session}/anat/sub-{subject}_{session}_run-{item:02d}_T1w"
    )

    # functional BOLD
    study_bold = create_key(
        "sub-{subject}/{session}/func/sub-{subject}_{session}_task-study_run-{item:02d}_bold"
    )
    roi_bold = create_key(
        "sub-{subject}/{session}/func/sub-{subject}_{session}_task-roi_run-{item:02d}_bold"
    )

    # diffusion
    dwi = create_key(
        "sub-{subject}/{session}/dwi/sub-{subject}_{session}_run-{item:02d}_dwi"
    )

    # field maps for func and dwi
    fmap_func = create_key(
        "sub-{subject}/{session}/fmap/sub-{subject}_{session}_acq-{acquisition}_dir-{direction}_epi"
    )
    fmap_dwi = create_key(
        "sub-{subject}/{session}/fmap/sub-{subject}_{session}_acq-{acquisition}_dir-{direction}_epi"
    )

    info = {
        t1w: [],
        study_bold: [],
        roi_bold: [],
        dwi: [],
        fmap_func: [],
        fmap_dwi: [],
    }

    for i, s in enumerate(seqinfo):
        xdim, ydim, slice_num, timepoints = (s[6], s[7], s[8], s[9])

        # let's do structural T1w first
        if (
            (slice_num == 176)
            and (timepoints == 1)
            and (
                "T1w_MPR_vNav" in s.series_description
            )  # t1w had normalized and non-normalized
            # and ("NORM" in s.image_type)  # Check if image_type contains 'NORM' for normalized
        ):
            next_scan = seqinfo[i + 1]
            if (
                next_scan[8] != slice_num
            ):  # if slice number is the same, saves the first t1w
                pass
            else:
                info[t1w].append([s[2]])

        # functional second
        elif "fMRI" in s[12]:
            if timepoints == 355:
                info[study_bold].append([s[2]])
            elif timepoints == 304:
                info[roi_bold].append([s[2]])
            elif timepoints == 1:
                if "PA" in s[12]:
                    info[fmap_func].append(
                        {
                            "item": s[2],
                            "direction": "PA",
                            "acquisition": "func",
                        }
                    )
                else:
                    info[fmap_func].append(
                        {"item": s[2], "direction": "AP", "acquisition": "func"}
                    )

        # diffusion third
        elif "dMRI" in s[12]:
            if timepoints == 103:
                info[dwi].append([s[2]])
            elif timepoints == 1 and s[12].endswith("PA_dMRI_REVL"):
                info[fmap_dwi].append(
                    {"item": s[2], "direction": "PA", "acquisition": "dwi"}
                )
            else:
                info[fmap_dwi].append(
                    {"item": s[2], "direction": "AP", "acquisition": "dwi"}
                )

    return info


"""# enable populate_intended_for for field maps (fmap_func, fmap_dwi)
POPULATE_INTENDED_FOR_OPTS = {
    "matching_parameters": ["PhaseEncodingDirection"],
    "criterion": "Closest",  # Match the closest scan based on these parameters
}
"""