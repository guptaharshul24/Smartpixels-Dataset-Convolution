#!/bin/bash
# ------------------------------------------------------------
# run_csa_stream.sh
# Usage: ./run_csa_stream.sh <input_file_name.gz>
# Description:
#  - Copies compressed .gz input file from EOS
#  - Unzips it
#  - Runs csa_effects_stream.py
#  - Compresses the output and copies back to EOS smartpix-box
# ------------------------------------------------------------

set -e  # Exit immediately on error

INPUT_GZ=$1
BASENAME=$(basename "$INPUT_GZ" .out.gz)
INPUT_FILE="${BASENAME}.out"
OUTPUT_FILE=convolved_output_${BASENAME}.out

# ---- Load environment ----
echo "=== Loading environment ==="
source /cvmfs/sft.cern.ch/lcg/views/LCG_105/x86_64-el9-gcc13-opt/setup.sh

# ---- Copy input from EOS ----
echo "=== Copying input from EOS ==="
xrdcp -f root://eosuser.cern.ch//eos/user/d/dshekar/dataset_3s_10ps/dataset_3s_10ps_50x12P5/${INPUT_GZ} .

# ---- Unzip input ----
echo "=== Unzipping input ==="
gunzip ${INPUT_GZ}

# ---- Copy pulse response CSV ----
echo "=== Copying pulse response CSV ==="
xrdcp -f root://eosuser.cern.ch//eos/user/h/harshul/convolution_datasets/pulse_response_cadence_diff_charges.csv .

# ---- Run CSA effects stream ----
echo "=== Running CSA Stream ==="
python3 csa_effects_stream.py ${INPUT_FILE} pulse_response_cadence_diff_charges.csv

# ---- Compress output and send directly to EOS ----
echo "=== Compressing and transferring output to EOS ==="
gzip ${OUTPUT_FILE}
xrdcp -f ${OUTPUT_FILE}.gz root://eosproject.cern.ch//eos/project/s/smartpix-box/pixelAV_datasets/unshuffled_DO_NOT_DELETE/temporary/preamp_response/

echo "=== Cleaning up local scratch ==="
rm -f *.gz pulse_response_cadence_diff_charges.csv


echo "=== Job completed successfully for ${BASENAME} ==="
