# -*- coding: utf-8 -*-

import copy
import ctypes
import fileinput
import itertools
import os
import qm
import argparse
import platform
import shutil
import multiprocessing
import time

from generate_qca_and_sim_from_structure_imp import generate_qca_and_sim_from_structure_imp
from generate_truth_from_sim_imp import generate_truth_from_sim_imp

from config import outdir


def print_timing(func):
    def wrapper(*arg):
        t1 = time.time()
        res = func(*arg)
        t2 = time.time()
        print('%s took %0.3f ms' % (getattr(func, '__name__'), (t2-t1)*1000.0))
        return res
    return wrapper


def composite_file_name(circuit_name, dir_idx=None, file_idx=None, appendix=None):
    path = os.path.join(outdir, circuit_name)
    if dir_idx is not None:
        path = os.path.join(path, str(dir_idx))
        if file_idx is not None:
            path = os.path.join(path, str(file_idx) + appendix)
    return os.path.normpath(os.path.abspath(path))


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
        if i < len(truth_values) - 1:
            if truth_values[i][:-1] == truth_values[i+1][:-1] and truth_values[i][-1] != truth_values[i+1][-1]:
                dc.append(tmp_val)
                i += 2
                continue
        if truth_values[i][-1] == 1:
            ones.append(tmp_val)
        else:
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
                tmp.append(labels[i] + "^")
        ret.append("*".join(tmp))
    return labels[-1] + " = " + " + ".join(ret)


class CircuitInfo(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_wchar_p),
        ("input_size", ctypes.c_int),
        ("output_size", ctypes.c_int),
        ("normal_size", ctypes.c_int),
        ("labels", ctypes.py_object),
        ("structure", ctypes.py_object),
        ("qca_file_path", ctypes.c_wchar_p),
        ("sim_file_path", ctypes.c_wchar_p),
        ("truth_table", ctypes.py_object),
        ("logic_expr", ctypes.py_object)

    ]


def simulate_circuit(circuit_info, args):
    assert(isinstance(args, dict))

    #prepare data used in generate_qca_and_sim_from_structure_imp
    design_name = circuit_info.name

    dir_idx = args["dir_idx"]
    file_idx = args["file_idx"]

    qca_file_name = composite_file_name(design_name, dir_idx, file_idx, ".qca")
    sim_file_name = composite_file_name(design_name, dir_idx, file_idx, ".sim")

    structure = args["structure"]

    #generate qca and sim file
    generate_qca_and_sim_from_structure_imp(structure, qca_file_name, sim_file_name)

    #truth table is computed in c++ extension code and has been sorted
    input_size = circuit_info.input_size
    truth_table = generate_truth_from_sim_imp(sim_file_name, input_size)

    #compute logic expression for each output index
    labels = circuit_info.labels
    output_idx = range(len(labels))[input_size:]

    logic_expr = []
    for out_idx in output_idx:
        truth_values = []
        for t in truth_table:
            truth_values.append(t[:input_size] + (t[out_idx],))

        expr = compute_logic_expression_from_truth_table(labels[:input_size] + [labels[out_idx]],
                                                         truth_values)
        logic_expr.append(expr)

    #compute is_correct
    is_correct = True
    if dir_idx != 0 or file_idx != 0:
        is_correct = set(circuit_info.truth_table) == set(truth_table)

    #save the computed result into database
    args["qca_file_path"] = qca_file_name
    args["sim_file_path"] = sim_file_name
    args["truth_table"] = truth_table
    args["logic_expr"] = logic_expr
    args["is_correct"] = is_correct

    return args


def load_benchmark(benchmark_file_name, circuit_info, args_list):
    assert(os.path.exists(benchmark_file_name))
    design_name = os.path.basename(benchmark_file_name)
    design_name = design_name[:design_name.find(".")]

    #clean the output directory
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    dbdir = os.path.join(outdir, design_name)
    if os.path.exists(dbdir):
        shutil.rmtree(dbdir)
    os.mkdir(dbdir)

    #compute the circuit infos
    structure = []
    for line in fileinput.input(benchmark_file_name):
        line_val = [int(x) for x in line.split("\t")]
        structure.append(line_val)

    input_size, output_size, normal_size, labels, normals = 0, 0, 0, [], []
    for r in range(len(structure)):
        for c in range(len(structure[r])):
            if structure[r][c] == 1:
                normal_size += 1
                normals.append((r, c))
            elif structure[r][c] == 0:
                continue
            elif structure[r][c] == -1:
                input_size += 1
                labels.append("I" + str(r) + str(c))
            elif structure[r][c] == -2:
                output_size += 1
                labels.append("O" + str(r) + str(c))

    labels.sort() #this order of labels is very important, so here comes a sorting

    #save the circuit infos into a shared memory variable
    circuit_info.name = design_name
    circuit_info.input_size = input_size
    circuit_info.output_size = output_size
    circuit_info.normal_size = normal_size
    circuit_info.labels = labels
    circuit_info.structure = structure

    #simulate the original circuit and save the other circuit infos
    benchmark_output_dir = composite_file_name(dbdir, 0)
    if not os.path.exists(benchmark_output_dir):
        os.mkdir(benchmark_output_dir)

    args = {"dir_idx": 0, "file_idx": 0, "structure": structure}
    simulate_circuit(circuit_info, args)

    circuit_info.qca_file_path = args["qca_file_path"]
    circuit_info.sim_file_path = args["sim_file_path"]
    circuit_info.truth_table = args["truth_table"]
    circuit_info.logic_expr = args["logic_expr"]

    #populate the args_list for all the other structures
    assert(isinstance(args_list, list))
    args_list.clear()

    for dir_idx in range(1, normal_size+1):
        cur_output_dir = composite_file_name(dbdir, dir_idx)
        if not os.path.exists(cur_output_dir):
            os.mkdir(cur_output_dir)

        combinations = itertools.combinations(normals, dir_idx)
        file_idx = 0
        for comb in combinations:
            cur_structure = copy.deepcopy(structure)
            for r, c in comb:
                cur_structure[r][c] = 0
            args_list.append({"dir_idx": dir_idx, "file_idx": file_idx,
                              "structure": cur_structure, "missing_indices": comb})
            file_idx += 1


@print_timing
def simulate_benchmark(benchmark_file_name):
    circuit_info = multiprocessing.Value(CircuitInfo)
    args_list = []

    load_benchmark(benchmark_file_name, circuit_info, args_list)

    processes = []
    for args in args_list:
        p = multiprocessing.Process(target=simulate_circuit, args=(circuit_info, args))
        processes.append(p)

    for p in processes:
        p.start()

    for p in processes:
        p.join()

if __name__ == "__main__":
    simulate_benchmark("/home/fpeng/Workspace/designer-mod/qcamod/benchmark/majority_gate_1.txt")
