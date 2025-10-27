# Smartpixels Dataset Stream Convolution Pipeline

This repository contains a fully automated **Condor-based pipeline** for performing **streamed convolution** of pixel cluster datasets with preamplifier pulse responses.  
It is designed for large-scale, high-throughput processing of detector simulation data on CERN computing infrastructure.

---

## Overview

The workflow automates the entire convolution process:
1. **Fetch compressed input datasets (`.out.gz`)** from EOS.
2. **Decompress and process** each file through the Python convolution script.
3. **Stream results** directly back to a CERN EOS project directory in compressed form (`.gz`).
4. **Run multiple jobs in parallel** using the HTCondor batch system.

The pipeline ensures minimal disk footprint on AFS and no redundant transfers of large files.

---

## Contents

- csa_effects_stream.py           [Main convolution script (streaming version)]
- helpers_stream.py               [Utility functions and helper routines]
- run_csa_stream.sh               [Execution script for a single Condor job]
- condor_csa_stream.sub           [HTCondor job submission file]
- input_files.txt                 [List of input .gz files to be processed]
- README.md                       [This documentation file]


---

## Workflow Details

### 1. Input Files
Each job takes a single compressed input cluster file, e.g.: pixel_clusters_d16401.out.gz

These are fetched from a dir stored on CERN eos storage.

### 2. Processing
The core script `csa_effects_stream.py`:
- Loads the charge clusters and corresponding pulse response CSV.  
- Performs convolution to simulate preamplifier response.  
- Writes the convolved cluster output to an `.out` file.

### 3. Output
Each output is automatically:
- Compressed to `.gz`
- Transferred directly to EOS: /eos/project/s/smartpix-box/pixelAV_datasets/unshuffled_DO_NOT_DELETE/temporary/preamp_response/

---

## Condor Job Configuration

The submission file `condor_csa_stream.sub` defines the HTCondor parameters:

```bash
universe   = vanilla
executable = /bin/bash
arguments  = -c "./run_csa_stream.sh $(input_file)"

should_transfer_files = YES
when_to_transfer_output = ON_EXIT
transfer_input_files = csa_effects_stream.py, helpers_stream.py, run_csa_stream.sh

output = logs/job_$(Cluster)_$(Process).out
error  = logs/job_$(Cluster)_$(Process).err
log    = logs/job_$(Cluster)_$(Process).log

request_memory  = 32 GB
request_disk    = 4 GB
request_cpus    = 2

+JobFlavour     = "longlunch"

queue input_file from input_files.txt
```
The file input_files.txt lists all .gz inputs, one per line.

## Run Instructions

Step 1 — Setup

Make sure the environment is configured with:

```
source /cvmfs/sft.cern.ch/lcg/views/LCG_105/x86_64-el9-gcc13-opt/setup.sh
```
Step 2 — Submit Jobs

```
condor_submit condor_csa_stream.sub
```
Step 3 — Monitor
```
condor_q $USER
```
Step 4 — Check Logs
Logs are written in the logs/ directory:
	•	job_*.out → stdout from the job
	•	job_*.err → error messages
	•	job_*.log → Condor event log

## Helper Scripts

run_csa_stream.sh
This is the per-job execution script that:
	•	Copies input from EOS
	•	Decompresses it
	•	Runs the Python convolution
	•	Compresses the output
	•	Streams it back to EOS

helpers_stream.py
Contains I/O and numerical utilities used by csa_effects_stream.py.

## Notifications
Each Condor job is configured to notify:
notify_user = username@cern.ch

## Quick Start (Local Test)

You can also test the pipeline on a single input file locally:
```
# Setup environment
source /cvmfs/sft.cern.ch/lcg/views/LCG_105/x86_64-el9-gcc13-opt/setup.sh

# Run on one input file
gunzip pixel_clusters_d16401.out.gz
python3 csa_effects_stream.py pixel_clusters_d16401.out pulse_response_cadence_diff_charges.csv
```

33Author

Harshul Gupta
CERN / SmartPixels Collaboration
📧 harshul.gupta@cern.ch
