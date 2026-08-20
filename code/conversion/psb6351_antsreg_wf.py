#!/usr/bin/env python

import os
from nipype.pipeline.engine import Workflow
from nipype.pipeline.engine import Node
from nipype.pipeline.engine import MapNode
from nipype.pipeline.engine import JoinNode
from nipype.interfaces.utility import IdentityInterface
from nipype.interfaces.utility import Function
from nipype.interfaces import fsl
from nipype.interfaces import ants
from glob import glob
from nipype.interfaces.io import DataSink
from mattfeld_utility_workflows.fs_skullstrip_util import create_freesurfer_skullstrip_workflow


fs_projdir = '/home/data/madlab/surfaces/emu'
projdir = '/home/data/madlab/data/mri/emu'
workdir = '/scratch/madlab/emu'
workingdir = os.path.join(workdir,'antsreg') #working directory
if not os.path.exists(workingdir):
    os.makedirs(workingdir)

fs_skullstrip_wf = create_freesurfer_skullstrip_workflow()
fs_skullstrip_wf.inputs.inputspec.subjects_dir = fs_projdir

sids = ['1023','1026','1027']

# Set up the FreeSurfer skull stripper work flow
antsreg_wf = Workflow(name='antsreg_wf')
antsreg_wf.base_dir = workingdir

subjID_infosource = Node(IdentityInterface(fields=['subject_id','subjects_dir']), name = 'subjID_infosource')
subjID_infosource.iterables = ('subject_id', sids)

antsreg_wf.connect(subjID_infosource, 'subject_id', fs_skullstrip_wf, 'inputspec.subject_id')

# Use a JoinNode to aggregrate all of the outputs from the fs_skullstrip_wf
reg = Node(ants.Registration(), name='antsRegister')
reg.inputs.fixed_image = '/home/data/madlab/data/mri/emu/study_template/antsTMPL_template.nii.gz'
reg.inputs.output_transform_prefix = "output_"
reg.inputs.transforms = ['Rigid', 'Affine', 'SyN']
reg.inputs.transform_parameters = [(0.1,), (0.1,), (0.2, 3.0, 0.0)]
reg.inputs.number_of_iterations = [[10000, 11110, 11110]] * 2 + [[100, 100, 50]]
reg.inputs.dimension = 3
reg.inputs.write_composite_transform = True
reg.inputs.collapse_output_transforms = True
reg.inputs.initial_moving_transform_com = True
reg.inputs.metric = ['Mattes'] * 2 + [['Mattes', 'CC']]
reg.inputs.metric_weight = [1] * 2 + [[0.5, 0.5]]
reg.inputs.radius_or_number_of_bins = [32] * 2 + [[32, 4]]
reg.inputs.sampling_strategy = ['Regular'] * 2 + [[None, None]]
reg.inputs.sampling_percentage = [0.3] * 2 + [[None, None]]
reg.inputs.convergence_threshold = [1.e-8] * 2 + [-0.01]
reg.inputs.convergence_window_size = [20] * 2 + [5]
reg.inputs.smoothing_sigmas = [[4, 2, 1]] * 2 + [[1, 0.5, 0]]
reg.inputs.sigma_units = ['vox'] * 3
reg.inputs.shrink_factors = [[3, 2, 1]]*2 + [[4, 2, 1]]
reg.inputs.use_estimate_learning_rate_once = [True] * 3
reg.inputs.use_histogram_matching = [False] * 2 + [True]
reg.inputs.winsorize_lower_quantile = 0.005
reg.inputs.winsorize_upper_quantile = 0.995
reg.inputs.float = True
reg.inputs.output_warped_image = 'output_warped_image.nii.gz'
reg.inputs.num_threads = 4
reg.plugin_args = {'bsub_args': '-R "span[hosts=1]" -n 4'}
antsreg_wf.connect(fs_skullstrip_wf, 'outputspec.skullstripped_file', reg, 'moving_image')

# Move the results to a designated results folder
datasink = Node(DataSink(), name="datasink")
datasink.inputs.base_directory = os.path.join(projdir, "norm_anat")
antsreg_wf.connect(subjID_infosource, 'subject_id', datasink, 'container')
antsreg_wf.connect(reg, 'composite_transform', datasink, 'anat2targ_xfm')
antsreg_wf.connect(reg, 'inverse_composite_transform', datasink, 'targ2anat_xfm')
antsreg_wf.connect(reg, 'warped_image', datasink, 'warped_image')

# Run the workflow
antsreg_wf.run(plugin='LSF', plugin_args={'bsub_args' : ('-q PQ_madlab')})

