# PSB6351 Fall 2022

Welcome to the Fall 2022 PSB6351 Cognitive Neuroscience Methods II course. This class focuses on cognitive neuroscience methods with an exclusive emphasis on magnetic resonance imaging (MRI).

Here you can find, work on, and submit materials for the class!

# Requirements

1) GitHub Account
2) Laptop

# Setting up your environment

# **!!! THIS IS ONLY FOR STUDENTS WHO DO NOT SET UP THEIR ACCOUNT THROUGH THEIR LAB !!!**
# **!!! STOP !!! DO NOT PROCEED IF YOU HAVE YOUR ENVIRONMENT SET UP !!!**

### The first command loads a miniconda software for creating conda virtual environment

1) module load miniconda3-4.5.11-oqs2mbgv3mmo3dll2f2rbxt4plfgyqzv

### The second command creates your conda environment with a specific version of python

2) conda create -p /home/##ADUSERNAME##/YOURLASTNAME_PSB6351/.envs/psb6351_environment python=3.9

### The next command activates your conda environment

3) conda activate /home/YOURADUSERNAME/YOURLASTNAME_PSB6351/.envs/psb6351_environment

### The next two commands install the packages you'll need to work with data

4) conda install nipype
5) conda install pandas

# Now setup your bash environment

### Add the following lines to your .bashrc file

prompt1="\[\e[0;33m\][\A]\[\e[0m\]" # Display the time in the bash prompt

prompt2="\[\e[1;39m\]\u@\h:\W\$\[\e[0m\]" # Add username@host:dir$

promptinfo=`${HOME}/.nodeload`

PROMPT_COMMAND='PS1="\[\e[1;37m\e[44m\]${project_name}\[\e[0;0m\]${prompt1}${promptinfo}${prompt2}"'

source /home/YOURADUSERNAME/YOURLASTNAME_PSB6351/code/.psb6351_env

# This stuff is super cool!!!
