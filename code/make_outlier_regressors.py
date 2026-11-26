#!/usr/bin/env python
"""
Build rapidart outlier ("spike") regressors for the 3dDeconvolve design matrix.

For every volume rapidart flagged as an outlier (frame-wise displacement above
threshold OR global-intensity spike > 3 SD), this makes one column that is 1 at
that volume and 0 everywhere else. Adding these columns to the GLM removes the
influence of those volumes on the beta estimates (equivalent to censoring them).

Runs are stacked in sorted order (run-01, run-02, ...) -- the SAME order the
functional files are given to 3dDeconvolve, so rows line up with the data.

Usage on the HPC (after psb6351_preproc.py has finished):
    python code/make_outlier_regressors.py loc       # localizer runs
    python code/make_outlier_regressors.py study     # study runs

Outputs (in derivatives/glm/sub-021/):
    sub-021_task-<task>_outlier_regressors.1D   -> pass to 3dDeconvolve -ortvec
    sub-021_task-<task>_censor.1D               -> 1 = keep, 0 = outlier (alternative)
"""
import os
import re
import sys
from glob import glob

import numpy as np

sid = 'sub-021'
task = sys.argv[1] if len(sys.argv) > 1 else 'loc'
thresh_folder = 'fwd05mm'   # use 'fwd1mm' for the 1 mm threshold

base_dir = '/home/aoste011/Mattfeld_PSB6351'
art_dir = os.path.join(base_dir, 'derivatives', 'preproc', sid, 'art', thresh_folder)
out_dir = os.path.join(base_dir, 'derivatives', 'glm', sid)
os.makedirs(out_dir, exist_ok=True)


def run_key(fname):
    """'.../norm.sub-021_task-loc_run-01_bold_volreg.txt' -> 'task-loc_run-01'"""
    m = re.search(r'(task-[A-Za-z0-9]+_run-\d+)', os.path.basename(fname))
    return m.group(1) if m else None


# norm files: one composite displacement value per volume -> gives run length
norm_files = sorted(glob(os.path.join(art_dir, '**', 'norm.*task-%s_*.txt' % task),
                         recursive=True), key=run_key)
outlier_files = {run_key(f): f for f in
                 glob(os.path.join(art_dir, '**', 'art.*task-%s_*_outliers.txt' % task),
                      recursive=True)}
if not norm_files:
    sys.exit('No rapidart norm files for task-%s in %s' % (task, art_dir))

run_lengths = []
spike_rows = []          # row index (in the concatenated time series) of each outlier
offset = 0
print('Threshold folder: %s   task-%s' % (thresh_folder, task))
for norm_file in norm_files:
    key = run_key(norm_file)
    nvol = len(np.loadtxt(norm_file))

    out_file = outlier_files.get(key)
    if out_file and os.path.getsize(out_file) > 0:
        idx = np.atleast_1d(np.loadtxt(out_file, dtype=int))   # 0-based volume indices
    else:
        idx = np.array([], dtype=int)

    print('  %-20s %3d / %3d volumes flagged (%.1f%%)'
          % (key, len(idx), nvol, 100.0 * len(idx) / nvol))
    spike_rows.extend(offset + idx)
    run_lengths.append(nvol)
    offset += nvol

total = offset
spike_rows = sorted(set(spike_rows))
print('  TOTAL: %d of %d volumes (%.1f%%)' % (len(spike_rows), total,
                                              100.0 * len(spike_rows) / total))

# Censor file (1 = keep, 0 = outlier) -- always written
censor = np.ones(total, dtype=int)
censor[spike_rows] = 0
censor_file = os.path.join(out_dir, '%s_task-%s_censor.1D' % (sid, task))
np.savetxt(censor_file, censor, fmt='%d')

# Spike regressors: one column per outlier volume
if spike_rows:
    spikes = np.zeros((total, len(spike_rows)), dtype=int)
    for col, row in enumerate(spike_rows):
        spikes[row, col] = 1
    spike_file = os.path.join(out_dir, '%s_task-%s_outlier_regressors.1D' % (sid, task))
    np.savetxt(spike_file, spikes, fmt='%d')
    print('Saved', spike_file, '(%d columns)' % spikes.shape[1])
else:
    print('No outliers -> no spike regressor file (leave -ortvec out of 3dDeconvolve)')
print('Saved', censor_file)
print('Run lengths (rows per run, in order):', run_lengths)
