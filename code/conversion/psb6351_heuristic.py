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

    keyname(e.g.t1w) = create_key('use/this/to/define/sub-{subject}/path/for/file')
    # note you should probably have a key for each scan you want to capture

    info = {
            keyname(e.g.t1w) : [],
           }

    for s in seqinfo:
        xdim, ydim, slice_num, timepoints = (s[6], s[7], s[8], s[9])
        if (slice_num == SOMENUMBER) and (timepoints == 1) and ("NAMEOFSCANTYPE" in s.series_description):
            info[keyname(e.g.t1w)].append(s[2])
        elif (slice_num > SOMEOTHERNUMBER) and (timepoints == SOMETHINGELSE) and ("DIFFERENTNAMEOFSCAN" in s[12]):
            info[?].append(s[2])
        else:
            pass
    return info
