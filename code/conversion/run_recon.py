#!/usr/bin/env python
from pathlib import Path
import subprocess as sp
from glob import glob


file_dir = Path(__file__).parent
# Produce freesurfer directory if it doesn't exist.
Path("/home/csted001/Mattfeld_PSB6351/derivatives/freesurfer").mkdir(
    exist_ok=True, parents=True
)

for subject_dir in Path("/home/csted001/Mattfeld_PSB6351/dset/").glob("sub-*"):
    subject = subject_dir.name.split('/')[-1]
    if Path(
        f"/home/csted001/Mattfeld_PSB6351/derivatives/freesurfer/{subject}"
    ).exists():
        continue
    print(subject)
    anat_img = (
        "/home/csted001/Mattfeld_PSB6351/dset/"
        f"{subject}/ses-1/anat/{subject}_run-2_T1w.nii.gz"
    )
    cmd = f"recon-all -all \
            -i {anat_img} \
            -subjid {subject} \
            -sd /home/csted001/Mattfeld_PSB6351/derivatives/freesurfer/"
    sp.Popen(
        f'sbatch -p classroom --account acc_psb6351 --qos pq_psb6351 -J recon_all_{subject} \
        -o /scratch/classroom/psb6351/csted001/crash/{subject}_reconall_out \
        --mail-type=END,FAIL --mail-user=csted001@fiu.edu \
        --wrap="{cmd}"',
        shell=True,
    )
