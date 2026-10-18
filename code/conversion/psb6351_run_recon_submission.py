#!/usr/bin/env python
# %%
import os
from pathlib import Path
import subprocess as sp
from glob import glob

#i had to update the script to work with the nipype connection script that i changed. it runs now, i have yet to plot the scan alignment/transformations
#this script was submitted as a cluster job (n = 20 cores) on 10/18 at ~5:50pm - hopefully finished computing in <12hrs (?)

os.environ['PATH'] += ':/home/applications/freesurfer/7.1/freesurfer/bin/'
os.environ['FREESURFER_HOME'] = '/home/applications/freesurfer/7.1/freesurfer'
file_dir = Path(__file__).parent
# Produce freesurfer directory if it doesn't exist.
Path("/home/eskog001/Mattfeld_PSB6351_eas/derivatives/freesurfer").mkdir(
    mode=0o777, exist_ok=True, parents=True
)
recon_codes = []
# Iterate over the subject directories after they have been bidsified
for subject_dir in Path("/home/eskog001/Mattfeld_PSB6351_eas/dset/").glob("sub-*"):
    # Just get the subject number
    subject = subject_dir.name.split('-')[1] # HOW DO YOU GET THE SUBJECT ID???? #split the dir name using ".name.split" to remove the dash/hyphen
    # If the subject already has a freesurfer directory don't run
    if Path(
        f"/home/eskog001/Mattfeld_PSB6351_eas/derivatives/freesurfer/sub-{subject}" #this prevents accidentally overwriting data per subject and wasting resources
    ).exists():
        continue
    print(subject)
    # the glob command below with the '?' allows for some flexibility
    # across when the structural scan was collected
    # for some participants it was collected during Session1 (S1)
    # while for others it was collecte during Session2 (S2)
    anat_img = sorted(glob(
        "/home/eskog001/Mattfeld_PSB6351_eas/dset/" #dataset root where the .nii.gz file lives (BIDS T1 file)
        f"sub-{subject}/anat/*T1w.nii.gz"
    ))[-1]
    cmd = f"recon-all -all \
            -i {anat_img} \
            -openmp 4 \
            -subjid sub-{subject} \
            -sd /home/eskog001/Mattfeld_PSB6351_eas/derivatives/freesurfer/"
    process = sp.Popen(
        f'sbatch --account acc_psb6351 --qos classroom \
            -J recon_all_{subject} -n 4 \
        -o /home/eskog001/Mattfeld_PSB6351_eas/code/conversion/run_recon_out/{subject}_reconall_out \
        --mail-type=END,FAIL --mail-user=eskog001@fiu.edu --wait \
        --wrap="{cmd}"',
        shell=True,
    )
    recon_codes.append(process)

