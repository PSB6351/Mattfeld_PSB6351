#!/bin/bash
#SBATCH --job-name=psb_preproc
#SBATCH --time=24:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=4gb
#SBATCH --account=acc_psb6351
#SBATCH --qos=classroom
# Outputs ----------------------------------
#SBATCH --output=/home/amele052/Mattfeld_PSB6351/preproc_assignment/crash/%x_%j_out.txt
#SBATCH --error=/home/amele052/Mattfeld_PSB6351/preproc_assignment/crash/%x_%j_err.txt
# ------------------------------------------

# load slurm so nipype can call sbatch for each node
module load slurm

# run the workflow with the python from the class environment
/home/amele052/Mattfeld_PSB6351/code/psb6351_environment/bin/python \
    /home/amele052/Mattfeld_PSB6351/code/psb6351_preproc.py