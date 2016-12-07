# -*- coding: utf-8 -*-

import copy
import fileinput
import itertools
import os
import csv
import qm
import argparse
import platform
import shutil
import threading

import generate_qca_and_sim_from_structure
import generate_truth_from_sim

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
            #print("generating structure file {0}".format(structure_file_name))
            write_structure_file(structure, structure_file_name)
            cnt += 1


generate_qca_and_sim_from_structure = generate_qca_and_sim_from_structure.generate_qca_and_sim_from_structure


###############################################################################
#############################logic related functions###########################
###############################################################################


generate_truth_from_sim = generate_truth_from_sim.generate_truth_from_sim


def compute_logic_expression_from_truth_table(labels, truth_values):
    input_size = len(labels)-1

    if len(truth_values) < 2**input_size:
        return "Not fully polarized"

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

def load_truth_file(truth_file_name):
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
    return labels, truth


def generate_logic_from_truth(truth_file_name, output_dir):
    #parse labels and truth values
    labels, truth = load_truth_file(truth_file_name)

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

        logic_expr = compute_logic_expression_from_truth_table(labels[:output_index[0]] + [labels[out_idx]],
                                                               truth_values)
        logic_exprs.append(logic_expr)

    #write logic expressions to file
    base_name = os.path.basename(truth_file_name)
    base_name = base_name[:base_name.find(".")]

    #print("generating logic file from {0}".format(truth_file_name))
    logic_file_name = os.path.abspath(os.path.join(output_dir, base_name+".logic"))
    with open(logic_file_name, 'w') as outf:
        for expr in logic_exprs:
            outf.write("{0}\n".format(expr))


###############################################################################


def visit_outdir(outdir, func, appendix):
    threads = []

    dir_names = os.listdir(outdir)
    for dir_name in dir_names:
        output_dir = os.path.normpath(os.path.join(outdir, dir_name))
        all_files = os.listdir(output_dir)
        
        needed_files = filter(lambda x: x.endswith(appendix), all_files)
        needed_file_names = [os.path.join(output_dir, needed_file) for needed_file in needed_files]
        for needed_file_name in needed_file_names:
            threads.append(threading.Thread(target=func,
                                            args=(os.path.normpath(os.path.abspath(needed_file_name)),
                                                  os.path.normpath(os.path.abspath(output_dir)))))
    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()



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

    import datetime
    starttime = datetime.datetime.now()

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

    endtime = datetime.datetime.now()
    interval = (endtime - starttime).seconds
    print("Totol running time: {0} seconds".format(interval))
