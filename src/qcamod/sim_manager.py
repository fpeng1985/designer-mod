# -*- coding: utf-8 -*-


import argparse
import os

from generate_simulation_files import generate_structures_from_benchmark, generate_qca_and_sim_from_structure
from generate_logic_files import generate_truth_from_sim, generate_logic_from_truth

###############################################################################

default_benchmark_file_name = r"C:\msys64\common\benchmark\qcasim\majority_gate_1.txt"
default_output_dir =r"C:\Users\fpeng\Documents\sim_manager"

parser = argparse.ArgumentParser(description="Specify the benchmark file")
parser.add_argument("-i", type=str, nargs='?', dest='benchmark_file_name', default=default_benchmark_file_name, help='benchmark file name')
parser.add_argument("-o", type=str, nargs='?', dest='outdir', default=default_output_dir, help='output file directory')

###############################################################################

def visit_outdir(outdir, func, appendix):
    dir_names = os.listdir(outdir)
    for dir_name in dir_names:
        output_dir = os.path.join(outdir, dir_name)
        all_files = os.listdir(output_dir)
        
        needed_files = filter(lambda x: x.endswith(appendix), all_files)
        needed_file_names = [os.path.join(output_dir, needed_file) for needed_file in needed_files]
        for needed_file_name in needed_file_names:
            func(os.path.abspath(needed_file_name), os.path.abspath(output_dir))

###############################################################################

if __name__ == "__main__":
    args = parser.parse_args()
    
    #make output files dir
    base_name = os.path.basename(args.benchmark_file_name)
    base_name = base_name[:base_name.find(".")]

    outdir = os.path.join(args.outdir, base_name)
    if not os.path.exists(outdir):
        os.mkdir(outdir)
    
    generate_structures_from_benchmark(args.benchmark_file_name, outdir)
    
    visit_outdir(outdir, generate_qca_and_sim_from_structure, ".txt")
    visit_outdir(outdir, generate_truth_from_sim, ".sim")
    visit_outdir(outdir, generate_logic_from_truth, ".truth")