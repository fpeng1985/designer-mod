# -*- coding: utf-8 -*-


import argparse
import os

from generate_simulation_files import generate_simulation_files
from generate_logic_files import generate_logic_files

###############################################################################

default_benchmark_file_name = r"C:\msys64\common\benchmark\qcasim\majority_gate_1.txt"
default_output_dir =r"C:\Users\fpeng\Documents\sim_manager"

parser = argparse.ArgumentParser(description="Specify the benchmark file")
parser.add_argument("-i", type=str, nargs='?', dest='benchmark_file_name', default=default_benchmark_file_name, help='benchmark file name')
parser.add_argument("-o", type=str, nargs='?', dest='output_dir', default=default_output_dir, help='output file directory')

###############################################################################

if __name__ == "__main__":
    args = parser.parse_args()
    
    #make output files dir
    base_name = os.path.basename(args.benchmark_file_name)
    base_name = base_name[:base_name.find(".")]

    outdir = os.path.join(args.output_dir, base_name)
    if not os.path.exists(outdir):
        os.mkdir(outdir)
    
    generate_simulation_files(args.benchmark_file_name, outdir)
    
    generate_logic_files(outdir)