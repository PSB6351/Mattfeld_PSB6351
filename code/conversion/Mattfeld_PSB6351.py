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
    t1w = create_key('sub-{subject}/ses-S{SESION}/anat/sub-{subject}_run-{item}_T1w')

    info = {
            # ADD KEYS FROM ABOVE AND EMPTY LISTS AS VALUES
            # IN THE INFO DICTIONARY...THIS WILL BE USED BELOW
            # TO ASSIGN THE CORRECT DICOMS TO THE RELEVANT SCANS
            t1w : [],
            ...,
           }

    for s in seqinfo:
        xdim, ydim, slice_num, timepoints = (s[6], s[7], s[8], s[9])
        if (slice_num == 176) and (timepoints == 1) and ("T1w_MPR_vNav" in s.series_description):
            info[t1w].append(s[2])
        elif (WHAT LOGICALS GO HERE) and (OR HERE) and (OR HERE): # TO UNIQUELY SELECT EACH SCAN
            info[WHAT UNIQUE SCAN KEY GOES HERE].append(s[2])
        # ADD REMAINING LOGICALS TO PARSE YOUR SCANS...
        else:
            pass
    return info
