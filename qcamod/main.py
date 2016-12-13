# -*- coding: utf-8 -*-

import argparse
import platform

from config import *
from models import load_benchmark, simulate_benchmark, generate_statistics

###############################################################################
#program options
default_benchmark_file_name = ""
default_output_dir = ""

if platform.system() == "Windows":
    default_benchmark_file_name = r"..\..\qcamod\benchmark\majority_gate_1.txt"
else:
    default_benchmark_file_name = "../../qcamod/benchmark/majority_gate_1.txt"

parser = argparse.ArgumentParser(description="Specify the benchmark file and output directory")
parser.add_argument("-i", type=str, nargs='?', dest='benchmark_file_name',
                    default=default_benchmark_file_name, help='benchmark file name')
parser.add_argument("-o", type=str, nargs='?', dest='outdir', default=OUT_DIR, help='output file directory')

###############################################################################

if __name__ == "__main__":

    import time
    start_time = time.time()

    args = parser.parse_args()

    OUT_DIR = args.outdir
    circuit_info, args_list = load_benchmark(args.benchmark_file_name)

    simulate_benchmark(circuit_info, args_list)
    generate_statistics(circuit_info)

    end_time = time.time()
    interval = end_time - start_time
    print("Total running time: %0.3f seconds" % interval)
