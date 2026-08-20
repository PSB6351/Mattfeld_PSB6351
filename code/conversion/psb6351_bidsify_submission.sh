#!/bin/bash

#SBATCH -J psb6351_dcm_convert
#SBATCH -o /home/amattfel/Mattfeld_PSB6351/code/conversion/out_dcm
#SBATCH -e /home/amattfel/Mattfeld_PSB6351/code/conversion/err_dcm
#SBATCH --qos # WHAT QOS
#SBATCH --account # WHAT ACCOUNT
#SBATCH --partition # WHAT PARITION

# SET UP A HEUDICONV CALL TO BIDSIFY YOUR DATA
# CAN YOU USE HEUDICONV WITHOUT AN OUTPUT TO HELP ESTABLISH YOUR HEURISTIC FILE?
# WHAT WOULD THE FINAL HEUDICONV SUBMISSION LOOK LIKE?
heudiconv
