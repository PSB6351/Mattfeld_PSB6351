#!/usr/bin/env python
# %%
import os
from pathlib import Path
import subprocess as sp
from glob import glob


os.environ['PATH'] += ':/home/applications/freesurfer/7.1/freesurfer/bin/'
os.environ['FREESURFER_HOME'] = '/home/applications/freesurfer/7.1/freesurfer'
file_dir = Path(__file__).parent

# My paths (the original pointed to /home/amattfel and had a typo: /home/amattfeld)
base_dir = Path("/home/aoste011/Mattfeld_PSB6351")
fs_dir = base_dir / "derivatives" / "freesurfer"

# Produce freesurfer directory if it doesn't exist.
fs_dir.mkdir(mode=0o777, exist_ok=True, parents=True)

# The SLURM -o directory must exist BEFORE submitting, otherwise
# the job has nowhere to write its output log (same issue as the crash dir)
out_dir = base_dir / "code" / "conversion" / "run_recon_out"
out_dir.mkdir(mode=0o777, exist_ok=True, parents=True)

recon_codes = []
# Iterate over the subject directories after they have been bidsified
for subject_dir in (base_dir / "dset").glob("sub-*"):
    # Just get the subject number
    # subject_dir.name gives 'sub-021' -> split on '-' and keep the number '021'
    subject = subject_dir.name.split("-")[-1]
    # If the subject already has a freesurfer directory don't run
    # MY ANSWER (what needs to exist / why it matters):
    #
    if Path(
        f"{fs_dir}/sub-{subject}"
    ).exists():
        continue
    print(subject)
    # the glob command below with the '?' allows for some flexibility
    # across when the structural scan was collected
    # for some participants it was collected during Session1 (S1)
    # while for others it was collecte during Session2 (S2)
    # MY ANSWER (which directory and file):
    #
    anat_img = sorted(glob(
        f"{base_dir}/dset/"
        f"sub-{subject}/anat/sub-{subject}*T1w.nii.gz"
    ))[-1]
    cmd = f"recon-all -all \
            -i {anat_img} \
            -openmp 4 \
            -subjid sub-{subject} \
            -sd {fs_dir}/"
    process = sp.Popen(
        f'sbatch --account acc_psb6351 --qos classroom \
            -J recon_all_{subject} -n 4 \
        -o {out_dir}/{subject}_reconall_out \
        --mail-type=END,FAIL --mail-user=aoste011@fiu.edu --wait \
        --wrap="{cmd}"',
        shell=True,
    )
    recon_codes.append(process)
