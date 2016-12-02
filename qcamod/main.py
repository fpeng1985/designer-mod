# -*- coding: utf-8 -*-

import copy
import fileinput
import itertools
import os
import csv
import qm
import argparse
import platform

from generate_qca_and_sim_from_structure import generate_qca_and_sim_from_structure
from generate_truth_from_sim import generate_truth_from_sim

###############################################################################
###################simulation related functions################################
###############################################################################


def load_structure_file(benchmark_file_name):
    circuit = []
    for line in fileinput.input(benchmark_file_name):
        vals = line.split("\t")
        circuit.append([int(val) for val in vals])

    normals = []
    for r in range(len(circuit)):
        for c in range(len(circuit[r])):
            if circuit[r][c] == 1:
                normals.append((r, c,))

    return circuit, normals


def write_structure_file(structure, structure_file_name):
    lines = []
    for row in structure:
        line = []
        for col in row:
            line.append(str(col))
        lines.append("\t".join(line)+"\n")
    with open(structure_file_name, 'w') as f:
        f.writelines(lines)


def generate_structures_from_benchmark(benchmark_file_name, outdir):
    assert(os.path.exists(outdir))

    #load benchmark circuit structure
    circuit, normals = load_structure_file(benchmark_file_name)

    #for each missing number make a dir, and generate files
    for i in range(len(normals)):
        output_dir = os.path.join(outdir, str(i+1))
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

        combinations = itertools.combinations(normals, i+1)

        cnt = 1
        for comb in combinations:
            #construct structure
            structure = copy.deepcopy(circuit)
            for r, c in comb:
                structure[r][c] = 0
            #write structure
            structure_file_name = os.path.abspath(os.path.join(output_dir, str(cnt)+".txt"))
            print("generating structure file {0}".format(structure_file_name))
            write_structure_file(structure, structure_file_name)
            cnt += 1



###############################################################################
#############################logic related functions###########################
###############################################################################


def compute_logic_expression_from_truth_table(labels, truth_values):
    input_size = len(labels)-1

    ones = []
    zeros = []
    dc = []
    i = 0
    while i < len(truth_values):
        tmp_val = 0
        for j in range(input_size):
            tmp_val += truth_values[i][j]*(2**(input_size-1-j))
        if i < len(truth_values) -1:
            if truth_values[i][:-1]==truth_values[i+1][:-1] and truth_values[i][-1] != truth_values[i+1][-1]:
                dc.append(tmp_val)
                i += 2
                continue
        if truth_values[i][-1] == 1:
            ones.append(tmp_val)
        else:#truth_values[i][-1] == 0
            zeros.append(tmp_val)
        i += 1

    terms = qm.qm(ones=ones, zeros=zeros, dc=dc)
    ret = []
    for term in terms:
        tmp = []
        for i in range(input_size):
            if term[i] == "1":
                tmp.append(labels[i])
            elif term[i] == "0":
                tmp.append(labels[i] + "'")
        ret.append("*".join(tmp))
    return labels[-1] + " = " + " + ".join(ret)


def generate_logic_from_truth(truth_file_name, output_dir):
    #parse labels and truth values
    labels = []
    truth = []
    with open(truth_file_name, 'r') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        labels = reader.fieldnames

        for row in reader:
            tmp = []
            for name in labels:
                tmp.append(int(row[name]))
            truth.append(tuple(tmp))
    truth.sort()

    #compute output index
    output_index = []
    for i in range(len(labels)):
        if labels[i].startswith("O"):
            output_index.append(i)

    #compute logic expression for each output index
    logic_exprs = []
    for out_idx in output_index:
        truth_values = []
        for t in truth:
            truth_values.append(t[:output_index[0]] + (t[out_idx],))

        logic_expr = compute_logic_expression_from_truth_table(labels[:output_index[0]] + [labels[out_idx]], truth_values)
        logic_exprs.append(logic_expr)

    #write logic expressions to file
    base_name = os.path.basename(truth_file_name)
    base_name = base_name[:base_name.find(".")]

    print("generating logic file from {0}".format(truth_file_name))
    logic_file_name = os.path.abspath(os.path.join(output_dir, base_name+".logic"))
    with open(logic_file_name, 'w') as outf:
        for expr in logic_exprs:
            outf.write("{0}\n".format(expr))


###############################################################################


###############################################################################
#program settings

default_benchmark_file_name = ""
default_output_dir = ""

if platform.system() == "Windows":
    default_benchmark_file_name = r"C:\msys64\common\benchmark\qcasim\majority_gate_2.txt"
    default_output_dir =r"C:\Users\fpeng\Documents\sim_manager"
    

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


if __name__ == "__main__":
    # generate_qca_and_sim_from_structure(r"C:\Users\fpeng\Documents\sim_manager\majority_gate_1\1\1.txt", r"C:\Users\fpeng\Documents\sim_manager\majority_gate_1\1")
    # generate_truth_from_sim(r"C:\Users\fpeng\Documents\sim_manager\majority_gate_1\1\1.sim", r"C:\Users\fpeng\Documents\sim_manager\majority_gate_1\1")
    # generate_logic_from_truth(r"C:\Users\fpeng\Documents\sim_manager\majority_gate_1\1\1.truth", r"C:\Users\fpeng\Documents\sim_manager\majority_gate_1\1")

    parser = argparse.ArgumentParser(description="Specify the benchmark file")
    parser.add_argument("-i", type=str, nargs='?', dest='benchmark_file_name', default=default_benchmark_file_name, help='benchmark file name')
    parser.add_argument("-o", type=str, nargs='?', dest='outdir', default=default_output_dir, help='output file directory')
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