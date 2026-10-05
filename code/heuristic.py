from __future__ import annotations


def create_key(template, outtype=('nii.gz',), annotation_classes=None):
    if template is None or not template:
        raise ValueError('Template must be a valid format string')
    return template, outtype, annotation_classes


# Section 1: keys

t1w = create_key(
    'sub-{subject}/anat/sub-{subject}_run-{item:03d}_T1w'
)

func_study1 = create_key(
    'sub-{subject}/func/sub-{subject}_task-REVL_run-01_bold'
)

func_study2 = create_key(
    'sub-{subject}/func/sub-{subject}_task-REVL_run-02_bold'
)

func_study3 = create_key(
    'sub-{subject}/func/sub-{subject}_task-REVL_run-03_bold'
)

func_study4 = create_key(
    'sub-{subject}/func/sub-{subject}_task-REVL_run-04_bold'
)

func_roi1 = create_key(
    'sub-{subject}/func/sub-{subject}_task-ROIloc_run-01_bold'
)

func_roi2 = create_key(
    'sub-{subject}/func/sub-{subject}_task-ROIloc_run-02_bold'
)

fmap_func_pa = create_key(
    'sub-{subject}/fmap/sub-{subject}_acq-func_dir-PA_epi'
)

fmap_func_ap = create_key(
    'sub-{subject}/fmap/sub-{subject}_acq-func_dir-AP_epi'
)

dwi = create_key(
    'sub-{subject}/dwi/sub-{subject}_dir-AP_dwi'
)

fmap_dwi_ap = create_key(
    'sub-{subject}/fmap/sub-{subject}_acq-dwi_dir-AP_epi'
)

fmap_dwi_pa = create_key(
    'sub-{subject}/fmap/sub-{subject}_acq-dwi_dir-PA_epi'
)


def infotodict(seqinfo):

    # Section 1b: info dictionary
    info = {
        t1w: [],
        func_study1: [],
        func_study2: [],
        func_study3: [],
        func_study4: [],
        func_roi1: [],
        func_roi2: [],
        fmap_func_pa: [],
        fmap_func_ap: [],
        dwi: [],
        fmap_dwi_ap: [],
        fmap_dwi_pa: [],
    }

    # Section 2: criteria
    for s in seqinfo:

        if (
            s.protocol_name == 'T1w_MPR_vNav'
            and s.dim1 == 256
            and s.dim3 == 176
        ):
            info[t1w].append(s.series_id)

        if s.protocol_name == 'fMRI_DistortionMap_PA':
            info[fmap_func_pa].append(s.series_id)

        if s.protocol_name == 'fMRI_DistortionMap_AP':
            info[fmap_func_ap].append(s.series_id)

        if (
            s.protocol_name == 'fMRI_REVL_ROI_loc_1'
            and not s.is_motion_corrected
        ):
            info[func_roi1].append(s.series_id)

        if (
            s.protocol_name == 'fMRI_REVL_ROI_loc_2'
            and not s.is_motion_corrected
        ):
            info[func_roi2].append(s.series_id)

        if (
            s.protocol_name == 'fMRI_REVL_Study_1'
            and not s.is_motion_corrected
        ):
            info[func_study1].append(s.series_id)

        if (
            s.protocol_name == 'fMRI_REVL_Study_2'
            and not s.is_motion_corrected
        ):
            info[func_study2].append(s.series_id)

        if (
            s.protocol_name == 'fMRI_REVL_Study_3'
            and not s.is_motion_corrected
        ):
            info[func_study3].append(s.series_id)

        if (
            s.protocol_name == 'fMRI_REVL_Study_4'
            and not s.is_motion_corrected
        ):
            info[func_study4].append(s.series_id)

        if s.protocol_name == 'dMRI_DistortionMap_AP_dMRI_REVL':
            info[fmap_dwi_ap].append(s.series_id)

        if s.protocol_name == 'dMRI_DistortionMap_PA_dMRI_REVL':
            info[fmap_dwi_pa].append(s.series_id)

        if s.protocol_name == 'dMRI_AP_REVL':
            info[dwi].append(s.series_id)

    return info
