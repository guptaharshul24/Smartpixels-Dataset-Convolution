"""
helpers.py — streaming-friendly version
Performs convolution per cluster without keeping all clusters in RAM.
"""

import numpy as np
import pandas as pd
import os

# ---------------------------------------------
# CONSTANTS
# ---------------------------------------------
E_CHARGE = 1.60217663e-19
TMIN = 50e-9   # start of pulse response
TMAX = 375e-9  # end of pulse response
T_STEP = np.float64(10e-12)  # 10 ps
SAVE_STEP = np.float64(200e-12)  # downsampled step (200 ps)
TRIM_MAX = 6e-9  # trim to 6 ns window

# ---------------------------------------------
# PULSE RESPONSE LOADING
# ---------------------------------------------
def load_pulse_responses(csv_file):
    """Load pulse response dataset and interpolate to common timestep."""
    print(f"Loading pulse response dataset from {csv_file} ...")
    df = pd.read_csv(csv_file, dtype=str, low_memory=False)

    times_cadence, voltages_cadence, charges_cadence = [], [], []

    n_pairs = int(len(df.columns) / 2)
    for i in range(n_pairs):
        if i % 20 == 0:
            print(f"   → Processing pulse {i+1}/{n_pairs} ...")

        try:
            charge_val = float(df.columns[i * 2 + 1].split(" ")[6])
        except Exception:
            charge_val = 0.0
        charges_cadence.append(charge_val)

        # Convert each pair safely to float arrays
        time_col = pd.to_numeric(df[df.columns[i * 2]], errors="coerce").dropna().to_numpy()
        volt_col = pd.to_numeric(df[df.columns[i * 2 + 1]], errors="coerce").dropna().to_numpy()
        if len(time_col) != len(volt_col) or len(time_col) == 0:
            continue

        mask = (time_col > TMIN) & (time_col < TMAX)
        time_clipped = time_col[mask]
        volt_clipped = volt_col[mask] - volt_col[mask][0]
        t_new = np.arange(time_clipped[0], time_clipped[-1], T_STEP)
        y_new = np.interp(t_new, time_clipped, volt_clipped)

        times_cadence.append(t_new)
        voltages_cadence.append(y_new)

    print(" → Pulse response dataset loaded.")
    return times_cadence, voltages_cadence, np.array(charges_cadence)

# ---------------------------------------------
# STREAMING CLUSTER READER
# ---------------------------------------------
def load_clusters_streaming(filename):
    """
    Generator version of load_clusters().
    Yields one cluster array and its metadata at a time.
    """
    print(f"Streaming clusters from {filename} ...")

    with open(filename, "r") as f:
        lines = []
        meta = None
        inside_cluster = False

        for line in f:
            if line.startswith("<cluster>"):
                if inside_cluster and lines:
                    yield parse_cluster_block(lines, meta)
                    lines = []
                inside_cluster = True
                meta = None
                continue

            if inside_cluster:
                if meta is None:
                    meta = line.strip().split()
                    continue
                lines.append(line)

        if inside_cluster and lines:
            yield parse_cluster_block(lines, meta)

def parse_cluster_block(lines, meta):
    """Parse one cluster block into a 3D NumPy array."""
    cluster_data = []
    current_slice = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("<time slice"):
            if current_slice:
                cluster_data.append(current_slice)
                current_slice = []
            continue
        elif stripped == "":
            continue
        else:
            current_slice.append(list(map(float, stripped.split())))

    if current_slice:
        cluster_data.append(current_slice)

    arr = np.array(cluster_data)
    arr = np.transpose(arr, (1, 2, 0))  # shape: (rows, cols, time_slices)
    return arr, meta

# ---------------------------------------------
# CONVOLUTION + SAVE
# ---------------------------------------------
def convolve_single_cluster(cluster, voltages_cadence, charges_cadence):
    """Perform convolution for a single cluster."""
    rows, cols, N = cluster.shape
    M = len(voltages_cadence[0])
    time_array = np.arange(N + M - 1) * T_STEP

    current_waveforms = np.empty((rows, cols, N))
    arr = np.empty((rows, cols, time_array.shape[0]))

    for i in range(rows):
        for j in range(cols):
            charge_injected = cluster[i, j][-1]
            closest_id = np.argmin(abs(charge_injected - charges_cadence))
            current = np.gradient(cluster[i, j] * E_CHARGE, T_STEP)
            y = np.convolve(current, voltages_cadence[closest_id]) * T_STEP
            current_waveforms[i, j] = current
            arr[i, j] = y*1000

    # Trim to 6 ns window
    mask = time_array <= TRIM_MAX
    arr = arr[:, :, mask]
    time_array = time_array[mask]

    # Downsample to 200 ps
    step = int(SAVE_STEP / T_STEP)
    arr = arr[:, :, ::step]

    return arr

def save_convolved_values(conv_clusters, input_file, output_file, meta, append=False):
    """Save convolved cluster arrays back to .out-style format, preserving header."""
    # If this is the first cluster, copy the header from input file
    if not append and os.path.exists(input_file):
        with open(input_file, "r") as fin, open(output_file, "w") as fout:
            for line in fin:
                # Copy all lines until first <cluster>
                if line.strip().startswith("<cluster>"):
                    break
                fout.write(line)
        # After writing header, we’ll append the first cluster
        mode = "a"
    else:
        # For subsequent clusters, always append
        mode = "a"

    # Now write the convolved cluster block
    with open(output_file, mode) as fout:
        fout.write("<cluster>\n")
        fout.write(" ".join(meta) + "\n")

        n_slices = conv_clusters.shape[2]
        for s in range(n_slices):
            time_ps = s * SAVE_STEP * 1e12
            fout.write(f"<time slice {time_ps:.6f} ps>\n")
            for i in range(conv_clusters.shape[0]):
                row_vals = " ".join(f"{v:.1f}" for v in conv_clusters[i, :, s])
                fout.write(row_vals + "\n")
