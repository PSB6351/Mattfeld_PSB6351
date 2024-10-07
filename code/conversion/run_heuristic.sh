#!/bin/bash

heudiconv -d /home/ssuss007/Mattfeld_PSB6351/sourcedata/{subject}/scans/*/resources/DICOM/files/*.dcm \
          -s Mattfeld_REVL-000-vCAT-021-S1 \
          -o /home/ssuss007/Mattfeld_PSB6351/dset/ \
          -f /home/ssuss007/Mattfeld_PSB6351/code/conversion/psb6351_heuristic.py \
          -c dcm2niix \
          --overwrite
