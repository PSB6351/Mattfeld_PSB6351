"""Iterate across tarballs and bidsify those that aren't in the dataset."""
#%%
import os
import json
import subprocess as sp
from pathlib import Path
import re
import shutil
import pandas as pd

script_dir = Path(__file__).parent

#subject_data = pd.read_csv(
#    "/home/amattfel/Mattfeld_PSB6351/code/conversion/sid_list.csv"
#)

if 'singularity-3.1' in os.environ['PATH']:
    os.environ['PATH'] = os.environ['PATH'].replace('/home/applications/singularity/singularity-3.1/bin', '/home/applications/singularity/singularity-3.5.3/bin/')
else:
    os.environ['PATH'] += ':/home/applications/singularity/singularity-3.5.3/bin/'
    
with open(script_dir / "Mattfeld_PSB6351.json", "r") as _:
    config = json.load(_)
# Iterates through tar.gz in sourcedata until one that hasn't been bidsified
bidsify_processes = []

for tar_file in sorted(list(Path("/home/amattfel/Mattfeld_PSB6351/sourcedata/").glob("*.tar.gz"))):
    check = tar_file.name
    
    # Find subject ID
    subject_match = re.search(r"(?P<subject>0[0-9]{2,2})", check)
    if subject_match:
        subject = subject_match.group("subject")
    else:
        continue
    # If subject and session exist in dataset, skip this tarball
    if os.path.exists(f"/home/amattfel/Mattfeld_PSB6351/dset/sub-{subject}/"):
        continue
    
    # Skip if subject is marked as excluded
    #if not subject_data[subject_data["exclude"].notnull()].query(f"id == {subject}").empty:
    #    continue
    
    print(subject)
    bidsify_workdir = Path(
        f'/scratch/madlab/bidsify_{config["project"]}/PSB6351-{subject}/'
    )
    bidsify_workdir.mkdir(mode=0o777, exist_ok=True, parents=True)

    # Make Heuristics and TAR File available in /scratch/ so singularity can read it
    heuristics = bidsify_workdir / os.path.basename(config["heuristics"])
    if not heuristics.is_file():
        shutil.copyfile(config["heuristics"], heuristics)
    tmp_tar_file = bidsify_workdir / "sourcedata" / tar_file.name
    if not tmp_tar_file.is_file():
        tmp_tar_file.parent.mkdir(exist_ok=True, parents=True)
        shutil.copyfile(tar_file, tmp_tar_file)
    output_dir = Path("/scratch/madlab/Mattfeld_PSB6351/bidsify_dset/")
    output_dir.mkdir(mode=0o777, parents=True, exist_ok=True)
    # Create bidsifier singularity cmd
    cmd = f'singularity run --cleanenv {config["bidsifier"]} \
         -d {tmp_tar_file} -f {heuristics} \
         -s {subject} -ss S1 -o {output_dir}'

    log_dir = "/home/amattfel/Mattfeld_PSB6351/code/conversion/bidsifier_logs"
    # Pass 'cmd' to sbatch for processing
    print(f'sbatch -J bidsify-{subject} -p investor --account iacc_madlab \
          --qos pq_madlab  --wait \
          -o {log_dir}/bidsify-{subject} \
          --wrap="{cmd}"')
    process = sp.Popen(
        f'sbatch -J bidsify-{subject} -p investor --account iacc_madlab \
          --qos pq_madlab  --wait \
          -o {log_dir}/bidsify-{subject} \
          --wrap="{cmd}"',
        shell=True,
    )
    bidsify_processes.append(process)
exit_codes = [p.wait() for p in bidsify_processes]

if any(exit_codes):
    raise ValueError('Targz job failed for one or more participants')
print(exit_codes)
print('Bidsify Complete')

