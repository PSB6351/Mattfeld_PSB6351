def create_key(template, outtype=('nii.gz',), annotation_classes=None):
    if template is None or not template:
        raise ValueError('Template must be a valid format string')
    return template, outtype, annotation_classes


def infotodict(seqinfo):

    # Anatomical scan
    t1w = create_key(
        'sub-{subject}/anat/sub-{subject}_T1w'
    )

    # fMRI distortion maps
    fmap_pa = create_key(
        'sub-{subject}/fmap/sub-{subject}_acq-fMRI_dir-PA_epi'
    )

    fmap_ap = create_key(
        'sub-{subject}/fmap/sub-{subject}_acq-fMRI_dir-AP_epi'
    )

    # ROI localizer
    roi = create_key(
        'sub-{subject}/func/sub-{subject}_task-ROI_run-{item:02d}_bold'
    )

    # Main REVL task
    revl = create_key(
        'sub-{subject}/func/sub-{subject}_task-REVL_run-{item:02d}_bold'
    )

    # Diffusion distortion maps
    dwi_fmap_ap = create_key(
        'sub-{subject}/fmap/sub-{subject}_acq-dMRI_dir-AP_epi'
    )

    dwi_fmap_pa = create_key(
        'sub-{subject}/fmap/sub-{subject}_acq-dMRI_dir-PA_epi'
    )

    # Diffusion scan
    dwi = create_key(
        'sub-{subject}/dwi/sub-{subject}_dir-AP_dwi'
    )

    info = {
        t1w: [],
        fmap_pa: [],
        fmap_ap: [],
        roi: [],
        revl: [],
        dwi_fmap_ap: [],
        dwi_fmap_pa: [],
        dwi: []
    }

    for s in seqinfo:

        # T1-weighted anatomical image
        if s.series_id.startswith('5-'):
            info[t1w].append(s.series_id)

        # fMRI distortion maps
        elif s.series_id.startswith('6-'):
            info[fmap_pa].append(s.series_id)

        elif s.series_id.startswith('7-'):
            info[fmap_ap].append(s.series_id)

        # ROI localizer runs
        elif s.series_id.startswith('8-') or s.series_id.startswith('9-'):
            info[roi].append(s.series_id)

        # REVL task runs
        elif (
            s.series_id.startswith('10-')
            or s.series_id.startswith('11-')
            or s.series_id.startswith('12-')
            or s.series_id.startswith('13-')
        ):
            info[revl].append(s.series_id)

        # dMRI distortion maps
        elif s.series_id.startswith('14-'):
            info[dwi_fmap_ap].append(s.series_id)

        elif s.series_id.startswith('15-'):
            info[dwi_fmap_pa].append(s.series_id)

        # diffusion scan
        elif s.series_id.startswith('16-'):
            info[dwi].append(s.series_id)

    return info

