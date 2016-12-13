# -*- coding: utf-8 -*-

import copy
import ctypes
import fileinput
import itertools
import os
import csv
import qm
import argparse
import platform
import shutil
import multiprocessing

import generate_qca_and_sim_from_structure
import generate_truth_from_sim

from config import *



def generate_statistics(benchmark_file_name, outdir):
    benchmark_name = os.path.basename(benchmark_file_name)
    benchmark_name = benchmark_name[:benchmark_name.find(".")]

    generate_qca_and_sim_from_structure(benchmark_file_name, outdir)
    generate_truth_from_sim(os.path.join(outdir, benchmark_name+".sim"), outdir)
    target_truth_file_name = os.path.join(outdir, benchmark_name+".truth")

    target_labels, target_truth = load_truth_file(target_truth_file_name)
    target_truth_set = set(target_truth)
    # with open(target_logic_file_name, 'r') as logic_file:
    #     lines = logic_file.readlines()
    #     target_logic_expr = lines[0]

    statistics = {}
    dir_names = os.listdir(outdir)
    dir_names = filter(lambda x: (x.find(".") == -1), dir_names)
    for dir_name in dir_names:
        dir_idx = int(dir_name)
        statistics[dir_idx] = {"total": 0, "right": 0, "wrong": 0, "error_rate": 0.0, "logic_exprs": {}}
        #logic_exprs is a mapping from a logic_expr to a list of index representing a file name

        output_dir = os.path.join(outdir, dir_name)
        all_files = os.listdir(output_dir)

        logic_exprs = {}
        logic_files = filter(lambda x: x.endswith(".logic"), all_files)
        for logic_file_name in logic_files:
            base_name = os.path.basename(logic_file_name)
            idx = int(base_name[:base_name.find(".")])

            with open(os.path.join(output_dir, logic_file_name), 'r') as logic_file:
                lines = logic_file.readlines()
                logic_exprs[idx] = lines[0].strip("\n")

        truth_files = filter(lambda x: x.endswith(".truth"), all_files)
        for truth_file_name in truth_files:
            base_name = os.path.basename(truth_file_name)
            idx = int(base_name[:base_name.find(".")])

            labels, truth = load_truth_file(os.path.join(output_dir, truth_file_name))
            truth_set = set(truth)

            assert(labels == target_labels)

            if truth_set == target_truth_set:
                statistics[dir_idx]["total"] += 1
                statistics[dir_idx]["right"] += 1
            else:
                statistics[dir_idx]["total"] += 1
                statistics[dir_idx]["wrong"] += 1
                if logic_exprs[idx] in statistics[dir_idx]["logic_exprs"]:
                    statistics[dir_idx]["logic_exprs"][logic_exprs[idx]].append(idx)
                else:
                    statistics[dir_idx]["logic_exprs"][logic_exprs[idx]] = [idx]

        statistics[dir_idx]["error_rate"] = statistics[dir_idx]["wrong"] / statistics[dir_idx]["total"]

    base_name = os.path.basename(outdir)
    with open(os.path.join(outdir, base_name+".statistics"), 'w') as statistics_file:
        for dir_idx in statistics.keys():
            output_dir = os.path.join(outdir, str(dir_idx))

            statistics_file.write("Missing Pattern : {0}\n".format(dir_idx))
            statistics_file.write("Total Number : {0}\n".format(statistics[dir_idx]["total"]))
            statistics_file.write("Error Number : {0}\n".format(statistics[dir_idx]["wrong"]))
            statistics_file.write("Error Rate : {0}\n".format(statistics[dir_idx]["error_rate"]))
            statistics_file.write("\n")

            for logic_expr in statistics[dir_idx]["logic_exprs"].keys():
                statistics_file.write("Logic exprssion {0} occured {1} times.\n".
                                      format(logic_expr, len(statistics[dir_idx]["logic_exprs"][logic_expr])))
                statistics_file.write("The qca file names for them are as follows :\n")
                for idx in statistics[dir_idx]["logic_exprs"][logic_expr]:
                    statistics_file.write("{0}\n".format(os.path.join(output_dir, str(idx)+".qca")))
                statistics_file.write("\n")

            statistics_file.write("\n========================================================================\n")

###############################################################################
#program options
default_benchmark_file_name = ""
default_output_dir = ""

if platform.system() == "Windows":
    default_benchmark_file_name = r"C:\msys64\common\benchmark\qcasim\majority_gate_1.txt"
    default_output_dir = r"C:\Users\fpeng\Documents\sim_manager"
else:
    default_benchmark_file_name = os.path.abspath("../../qcamod/benchmark/majority_gate_1.txt")
    default_output_dir = os.path.abspath("./sim_output")

parser = argparse.ArgumentParser(description="Specify the benchmark file and output directory")
parser.add_argument("-i", type=str, nargs='?', dest='benchmark_file_name', default=default_benchmark_file_name, help='benchmark file name')
parser.add_argument("-o", type=str, nargs='?', dest='outdir', default=default_output_dir, help='output file directory')

###############################################################################

if __name__ == "__main__":
    # generate_qca_and_sim_from_structure(r"C:\Users\fpeng\Documents\sim_manager\majority_gate_1\1\1.txt", r"C:\Users\fpeng\Documents\sim_manager\majority_gate_1\1")
    # generate_truth_from_sim(r"C:\Users\fpeng\Documents\sim_manager\majority_gate_1\1\1.sim", r"C:\Users\fpeng\Documents\sim_manager\majority_gate_1\1")
    # generate_logic_from_truth(r"C:\Users\fpeng\Documents\sim_manager\majority_gate_1\1\1.truth", r"C:\Users\fpeng\Documents\sim_manager\majority_gate_1\1")

    import time
    starttime = time.time()

    args = parser.parse_args()
    
    #make output files dir
    base_name = os.path.basename(args.benchmark_file_name)
    base_name = base_name[:base_name.find(".")]

    outdir = os.path.join(args.outdir, base_name)
    if os.path.exists(outdir):
        shutil.rmtree(outdir)
    os.mkdir(outdir)

    generate_structures_from_benchmark(args.benchmark_file_name, outdir)

    print("generating qca and sim start")
    visit_outdir(outdir, generate_qca_and_sim_from_structure, ".txt")
    print("generating qca and sim finished")

    print("generating truth start")
    visit_outdir(outdir, generate_truth_from_sim, ".sim")
    print("generating truth finished")

    print("generating logic start")
    visit_outdir(outdir, generate_logic_from_truth, ".truth")
    print("generating logic finished")

    print("generating statistics start")
    generate_statistics(args.benchmark_file_name, outdir)
    print("generating statistics finished")

    endtime = time.time()
    interval = endtime - starttime
    print("Totol running time: {0} seconds".format(interval))
