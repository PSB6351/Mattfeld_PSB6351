#!/usr/bin/env python
# %%
import os
from pathlib import Path
import subprocess as sp
from glob import glob


os.environ['PATH'] += ':/home/applications/freesurfer/7.1/freesurfer/bin/'
os.environ['FREESURFER_HOME'] = '/home/applications/freesurfer/7.1/freesurfer'
file_dir = Path(__file__).parent

# setting my own path
user_dir = "/home/sfrai003/Mattfeld_PSB6351"
freesurfer_dir = Path(f"{user_dir}/derivatives/freesurfer")
freesurfer_dir.mkdir(mode=0o777, exist_ok=True, parents=True)


Path(f"{user_dir}/code/conversion/run_recon_out").mkdir(mode=0o777, exist_ok=True, parents=True)

#Produce freesurfer directory if it doesn't exist.
#Path("/home/amattfeld/Mattfeld_PSB6351/derivatives/freesurfer").mkdir(
#    mode=0o777, exist_ok=True, parents=True
#)

recon_codes = []

# Iterate over the subject directories after they have been bidsified
for subject_dir in Path(f"{user_dir}/dset/").glob("sub-*"):
    # Just get the subject number
    #subject = "021"
    # If the subject already has a freesurfer directory don't run
    subject = subject_dir.name.split('-')[1]

    if Path(f"{freesurfer_dir}/sub-{subject}").exists():
        continue
    
    print(subject)
    # the glob command below with the '?' allows for some flexibility
    # across when the structural scan was collected
    # for some participants it was collected during Session1 (S1)
    # while for others it was collecte during Session2 (S2)
    
    anat_img = sorted(glob(
        f"{user_dir}/dset/sub-{subject}/ses-S?/anat/*_T1w.nii.gz"
    ))[-1]

    cmd = f"recon-all -all \
            -i {anat_img} \
            -openmp 4 \
            -subjid sub-{subject} \
            -sd {freesurfer_dir}"

    process = sp.Popen(
        f'sbatch -p highmem1-sapphirerapids --account acc_madlab --qos highmem1 \
            -J recon_all_{subject} -n 4 \
        -o {user_dir}/code/conversion/run_recon_out/{subject}_reconall_out \
        --mail-type=END,FAIL --mail-user=sfrai003@fiu.edu --wait \
        --wrap="{cmd}"',
        shell=True,
    )
    recon_codes.append(process)

