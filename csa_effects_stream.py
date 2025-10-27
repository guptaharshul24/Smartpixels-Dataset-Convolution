"""
csa_effects.py — Streaming CSA convolution runner
"""

import os
from helpers_stream import (
    load_pulse_responses,
    load_clusters_streaming,
    convolve_single_cluster,
    save_convolved_values,
)

#def post_CSA_clusters(cluster_file, pulse_csv, output_dir):
def post_CSA_clusters(cluster_file, pulse_csv):
    """Main entry point for post-CSA convolution."""
    print(f"\n→ Starting CSA convolution for file: {cluster_file}")

    # Load pulse responses
    times_cadence, voltages_cadence, charges_cadence = load_pulse_responses(pulse_csv)

    #os.makedirs(output_dir, exist_ok=True)
    input_base = os.path.splitext(os.path.basename(cluster_file))[0]
    #output_file = os.path.join(output_dir, f"convolved_output_{input_base}.out")
    output_file = f"convolved_output_{input_base}.out"

    # Process each cluster one by one (streaming)
    for idx, (cluster, meta) in enumerate(load_clusters_streaming(cluster_file)):
        print(f" → Processing cluster {idx}")
        conv_cluster = convolve_single_cluster(cluster, voltages_cadence, charges_cadence)

        # Only the first cluster should trigger header copy (append=False)
        append_flag = idx != 0
        save_convolved_values(conv_cluster, cluster_file, output_file, meta, append=append_flag)

    print(f"\n All clusters processed and saved to {output_file}")


if __name__ == "__main__":
    import sys
    #if len(sys.argv) != 4:
    if len(sys.argv) != 3:
        #print("Usage: python3 csa_effects.py <input_cluster_file.out> <pulse_response.csv> <output_dir>")
        print("Usage: python3 csa_effects.py <input_cluster_file.out> <pulse_response.csv>")
        sys.exit(1)

    cluster_file = sys.argv[1]
    pulse_csv = sys.argv[2]
   #output_dir = sys.argv[3]
    #post_CSA_clusters(cluster_file, pulse_csv, output_dir)
    post_CSA_clusters(cluster_file, pulse_csv)
