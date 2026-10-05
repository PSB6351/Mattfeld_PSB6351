from __future__ import annotations

import logging
from typing import Optional

from heudiconv.utils import SeqInfo

lgr = logging.getLogger("heudiconv")


def create_key(
    template: Optional[str],
    outtype: tuple[str, ...] = ("nii.gz",),
    annotation_classes: None = None,
) -> tuple[str, tuple[str, ...], None]:
    if template is None or not template:
        raise ValueError("Template must be a valid format string")
    return (template, outtype, annotation_classes)


def infotodict(
    seqinfo: list[SeqInfo],
) -> dict[tuple[str, tuple[str, ...], None], list[str]]:
    """Heuristic evaluator for determining which runs belong where

    allowed template fields - follow python string module:

    item: index within category
    subject: participant id
    seqitem: run number during scanning
    subindex: sub index within group
    """

    data = create_key("run{item:03d}")
        # Section 1: These key definitions should be revised by the user
    t1w_run1 = create_key('sub-{subject}/anat/sub-{subject}_run-01_T1w')
    t1w_run2 = create_key('sub-{subject}/anat/sub-{subject}_run-02_T1w')

    func_study1 = create_key('sub-{subject}/func/sub-{subject}_task-REVL_run-01_bold')
    func_study2 = create_key('sub-{subject}/func/sub-{subject}_task-REVL_run-02_bold')
    func_study3 = create_key('sub-{subject}/func/sub-{subject}_task-REVL_run-03_bold')
    func_study4 = create_key('sub-{subject}/func/sub-{subject}_task-REVL_run-04_bold')
    func_roi1 = create_key('sub-{subject}/func/sub-{subject}_task-ROIloc_run-01_bold')
    func_roi2 = create_key('sub-{subject}/func/sub-{subject}_task-ROIloc_run-02_bold')

    fmap_func_pa = create_key('sub-{subject}/fmap/sub-{subject}_acq-func_dir-PA_epi')
    fmap_func_ap = create_key('sub-{subject}/fmap/sub-{subject}_acq-func_dir-AP_epi')

    dwi = create_key('sub-{subject}/dwi/sub-{subject}_dir-AP_dwi')
    fmap_dwi_ap = create_key('sub-{subject}/fmap/sub-{subject}_acq-dwi_dir-AP_epi')
    fmap_dwi_pa = create_key('sub-{subject}/fmap/sub-{subject}_acq-dwi_dir-PA_epi')
    # Section 1b: This data dictionary (below) should be revised by the user.
    info = {t1w_run1: [], t1w_run2: [],
            func_study1: [], func_study2: [], func_study3: [], func_study4: [],
            func_roi1: [], func_roi2: [],
            fmap_func_pa: [], fmap_func_ap: [],
            dwi: [], fmap_dwi_ap: [], fmap_dwi_pa: []}

    # The following line does no harm, but it is not part of the dictionary.
    last_run = len(seqinfo)

    for s in seqinfo:
        """
        The namedtuple `s` contains the following fields:

        * total_files_till_now
        * example_dcm_file
        * series_id
        * dcm_dir_name
        * unspecified2
        * unspecified3
        * dim1
        * dim2
        * dim3
        * dim4
        * TR
        * TE
        * protocol_name
        * is_motion_corrected
        * is_derived
        * patient_id
        * study_description
        * referring_physician_name
        * series_description
        * image_type
        """

            # Section 2: These criteria should be revised by the user.
        # Dimension 3 must equal 176 and the protocol_name must match.
        # image_type is a tuple, so test for an exact element (the page's Tuples section).
        if (s.dim3 == 176) and ('T1w_MPR_vNav' == s.protocol_name) and ('NORM' not in s.image_type):
            info[t1w_run1].append(s.series_id)
        if (s.dim3 == 176) and ('T1w_MPR_vNav' == s.protocol_name) and ('NORM' in s.image_type):
            info[t1w_run2].append(s.series_id)

        if ('fMRI_DistortionMap_PA' == s.protocol_name):
            info[fmap_func_pa].append(s.series_id)
        if ('fMRI_DistortionMap_AP' == s.protocol_name):
            info[fmap_func_ap].append(s.series_id)

        # is_motion_corrected must be False, so we do not get a motion-corrected series.
        if ('fMRI_REVL_ROI_loc_1' == s.protocol_name) and (not s.is_motion_corrected):
            info[func_roi1].append(s.series_id)
        if ('fMRI_REVL_ROI_loc_2' == s.protocol_name) and (not s.is_motion_corrected):
            info[func_roi2].append(s.series_id)

        if ('fMRI_REVL_Study_1' == s.protocol_name) and (not s.is_motion_corrected):
            info[func_study1].append(s.series_id)
        if ('fMRI_REVL_Study_2' == s.protocol_name) and (not s.is_motion_corrected):
            info[func_study2].append(s.series_id)
        if ('fMRI_REVL_Study_3' == s.protocol_name) and (not s.is_motion_corrected):
            info[func_study3].append(s.series_id)
        if ('fMRI_REVL_Study_4' == s.protocol_name) and (not s.is_motion_corrected):
            info[func_study4].append(s.series_id)

        if ('dMRI_DistortionMap_AP_dMRI_REVL' == s.protocol_name):
            info[fmap_dwi_ap].append(s.series_id)
        if ('dMRI_DistortionMap_PA_dMRI_REVL' == s.protocol_name):
            info[fmap_dwi_pa].append(s.series_id)

        if ('dMRI_AP_REVL' == s.protocol_name):
            info[dwi].append(s.series_id)
    return info
