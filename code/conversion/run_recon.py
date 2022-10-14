#!/usr/bin/env python
from pathlib import Path
import subprocess as sp
from glob import glob

#aaron says go
file_dir = Path(__file__).parent
# Produce freesurfer directory if it doesn't exist.
Path("/home/amattfel/Mattfeld_PSB6351/derivatives/freesurfer").mkdir(
    exist_ok=True, parents=True
)

for subject_dir in Path("/home/amattfel/Mattfeld_PSB6351/dset/").glob("sub-*"):
    subject = subject_dir.name.split('/')[-1]
    if Path(
        f"/home/amattfel/Mattfeld_PSB6351/derivatives/freesurfer/{subject}"
    ).exists():
        continue
    print(subject)
    anat_img = (
        "/home/amattfel/Mattfeld_PSB6351/dset/"
        f"{subject}/anat/{subject}_run-2_T1w.nii.gz"
    )
    cmd = f"recon-all -all \
            -i {anat_img} \
            -subjid {subject} \
            -sd /home/amattfel/Mattfeld_PSB6351/derivatives/freesurfer/"
    sp.Popen(
        f'sbatch -p classroom --account acc_psb6351 --qos pq_psb6351 -J recon_all_{subject} \
        -o /scratch/classroom/psb6351/amattfel/crash/{subject}_reconall_out \
        --mail-type=END,FAIL --mail-user=amattfel@fiu.edu \
        --wrap="{cmd}"',
        shell=True,
    )
