import os

# LOCALIZER-ONLY heuristic for the final paper (V1 / V2 / FFA ROI analysis)
# copy of Mattfeld_PSB6351.py with only the scans this analysis needs:
#   - task-loc runs 1-2   (the data being analyzed)
#   - fMRI AP / PA distortion maps (optional TOPUP distortion correction)
# left out on purpose:
#   - T1w            -> already converted + FreeSurfer recon-all finished
#   - task-study 1-4 -> not used by the localizer analysis (study run-2 is where the
#                       original conversion crashed)
#   - dMRI + dMRI distortion maps -> not used

def create_key(template, outtype=('nii.gz',), annotation_classes=None):
    if template is None or not template:
        raise ValueError('Template must be a valid format string')
    return template, outtype, annotation_classes

def infotodict(seqinfo):
    """Heuristic evaluator for determining which runs belong where"""

    fun_loc = create_key('sub-{subject}/func/sub-{subject}_task-loc_run-{item}_bold')
    map_ap_fun = create_key('sub-{subject}/fmap/sub-{subject}_dir-AP_run-{item}_epi')
    map_pa_fun = create_key('sub-{subject}/fmap/sub-{subject}_dir-PA_run-{item}_epi')

    info = {
            fun_loc : [],
            map_ap_fun : [],
            map_pa_fun : []
           }

    for s in seqinfo:
        xdim, ydim, slice_num, timepoints = (s[6], s[7], s[8], s[9])

        if (slice_num == 66) and (timepoints == 304) and ("fMRI_REVL_ROI_loc" in s.series_description):
            info[fun_loc].append(s[2])

        elif (slice_num == 66) and (timepoints == 1) and ("fMRI_DistortionMap" in s.series_description) and ("AP" in s.series_description):
            info[map_ap_fun].append(s[2])

        elif (slice_num == 66) and (timepoints == 1) and ("fMRI_DistortionMap" in s.series_description) and ("PA" in s.series_description):
            info[map_pa_fun].append(s[2])

        else:
            pass

    return info
