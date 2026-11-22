#!/usr/bin/env python
# Counts frame-wise displacement (FWD) outlier timepoints per run
# at 1mm and 0.5mm, using the rapidart outputs saved by psb6351_preproc.py.
# Run on the HPC after the pipeline finishes:  python count_outliers.py

import os
import json
from glob import glob
import numpy as np

sid = 'sub-021'
art_dir = os.path.join('/home/aoste011/Mattfeld_PSB6351/derivatives/preproc', sid, 'art')

for folder, thresh in [('fwd1mm', 1.0), ('fwd05mm', 0.5)]:
    print('\n===== Threshold: %.1f mm FWD =====' % thresh)
    total = 0
    norm_files = sorted(glob(os.path.join(art_dir, folder, '**', 'norm.*.txt'), recursive=True))
    for norm_file in norm_files:
        fwd = np.loadtxt(norm_file)                 # one FWD value (mm) per volume
        n_out = int(np.sum(fwd > thresh))
        total += n_out
        run = os.path.basename(norm_file).replace('norm.', '').replace('.txt', '')
        print('%-60s  %3d / %d volumes (%.1f%%)  max FWD = %.2f mm'
              % (run, n_out, len(fwd), 100.0 * n_out / len(fwd), fwd.max()))

        # Cross-check against rapidart's own count (motion-only + motion&intensity)
        stats_file = norm_file.replace('norm.', 'stats.')
        if os.path.exists(stats_file):
            try:
                stats = json.load(open(stats_file))
                counts = [d for d in stats if 'motion_outliers' in d][0]
                art_n = counts['motion_outliers'] + counts['common_outliers']
                print('%-60s  rapidart says: %d' % ('', art_n))
            except Exception:
                pass
    print('TOTAL across runs: %d' % total)
