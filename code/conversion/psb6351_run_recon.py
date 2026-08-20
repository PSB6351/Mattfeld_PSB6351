#!/usr/bin/env python
# %%
import os
from pathlib import Path
import subprocess as sp
from glob import glob


os.environ['PATH'] += ':/home/applications/freesurfer/7.1/freesurfer/bin/'
os.environ['FREESURFER_HOME'] = '/home/applications/freesurfer/7.1/freesurfer'
file_dir = Path(__file__).parent
# Produce freesurfer directory if it doesn't exist.
Path("/home/amattfeld/Mattfeld_PSB6351/derivatives/freesurfer").mkdir(
    mode=0o777, exist_ok=True, parents=True
)
recon_codes = []
# Iterate over the subject directories after they have been bidsified
for subject_dir in Path("/home/amattfel/Mattfeld_PSB6351/dset/").glob("sub-*"):
    # Just get the subject number
    subject = # HOW DO YOU GET THE SUBJECT ID????
    # If the subject already has a freesurfer directory don't run
    if Path(
        f"WHAT NEEDS TO EXIST FOR THIS TO BE TRUE/FALSE...WHY DOES THAT MATTER?"
    ).exists():
        continue
    print(subject)
    # the glob command below with the '?' allows for some flexibility
    # across when the structural scan was collected
    # for some participants it was collected during Session1 (S1)
    # while for others it was collecte during Session2 (S2)
    anat_img = sorted(glob(
        "/home/amattfel/Mattfeld_PSB6351/WHAT DIRECTORY SHOULD I LOOK IN?/"
        f"sub-{subject}/anat/WHAT FILE DO I WANT HERE????"
    ))[-1]
    cmd = f"recon-all -all \
            -i {anat_img} \
            -openmp 4 \
            -subjid sub-{subject} \
            -sd /home/amattfel/Mattfeld_PSB6351/derivatives/freesurfer/"
    process = sp.Popen(
        f'sbatch -p WHAT PARTITION --account WHAT ACCOUNT --qos WHAT QOS \
            -J recon_all_{subject} -n 4 \
        -o /home/amattfel/Mattfeld_PSB6351/code/conversion/run_recon_out/{subject}_reconall_out \
        --mail-type=END,FAIL --mail-user=YOUREMAILAD@fiu.edu --wait \
        --wrap="{cmd}"',
        shell=True,
    )
    recon_codes.append(process)

