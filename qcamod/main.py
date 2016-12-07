# -*- coding: utf-8 -*-

from app import *
from models import *

import os
import fileinput
import itertools
import copy
import shutil
import qm
import math
import threading
import argparse

from generate_qca_and_sim_from_structure_imp import generate_qca_and_sim_from_structure_imp
from generate_truth_from_sim_imp import generate_truth_from_sim_imp

import peewee

########################################################################################
##################################helper functions######################################
########################################################################################


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
                tmp.append(labels[i] + "^")
        ret.append("*".join(tmp))
    return labels[-1] + " = " + " + ".join(ret)


########################################################################################
##################################main functions#######################################
########################################################################################


def load_benchmark(benchmark_file_name):
    name = os.path.basename(benchmark_file_name)
    name = name[:name.find(".")]

    circuit_dir = composite_file_name(name)
    if os.path.exists(circuit_dir):
        shutil.rmtree(circuit_dir)
        os.mkdir(circuit_dir)

    structure = []
    for line in fileinput.input(benchmark_file_name):
        line_val = [int(x) for x in line.split("\t")]
        structure.append(line_val)

    input_size = 0
    output_size = 0
    normal_size = 0
    labels = []
    normals = []
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

    #this order of labels is very important, so here comes a sorting
    labels.sort()

    circuit,created = CircuitInfo.get_or_create(name=name,
                                                defaults={"input_size": input_size, "output_size": output_size,
                                                          "normal_size": normal_size, "labels": labels})
    circuit.save()

    for dir_idx in range(normal_size+1):
        file_name = composite_file_name(name, dir_idx)
        os.mkdir(composite_file_name(name, dir_idx))

        combinations = itertools.combinations(normals, dir_idx)
        file_idx = 0
        for comb in combinations:
            cur_structure = copy.deepcopy(structure)
            for r, c in comb:
                cur_structure[r][c] = 0
            # print("{0} {1}".format(dir_idx, file_idx))
            sim_result, created = SimResult.get_or_create(circuit=circuit, dir_idx=dir_idx, file_idx=file_idx,
                                                          defaults={"structure": cur_structure, "missing_indices": comb})
            sim_result.save()

            file_idx += 1


def generate_qca_and_sim_from_structure(name, dir_idx, file_idx):
    circuit = CircuitInfo.get(CircuitInfo.name == name)
    sim_result = SimResult.get(SimResult.circuit == circuit,
                               SimResult.dir_idx == dir_idx, SimResult.file_idx == file_idx)

    structure = sim_result.structure
    qca_file_name = composite_file_name(name, dir_idx, file_idx, ".qca")
    sim_file_name = composite_file_name(name, dir_idx, file_idx, ".sim")

    generate_qca_and_sim_from_structure_imp(structure, qca_file_name, sim_file_name)

    #update database
    qca_file_name = composite_file_name(name, dir_idx, file_idx, ".qca")
    sim_file_name = composite_file_name(name, dir_idx, file_idx, ".sim")
    sim_result.qca_file_path = qca_file_name
    sim_result.sim_file_path = sim_file_name
    sim_result.save()


def generate_truth_and_logic_from_sim(name, dir_idx, file_idx):
    circuit = CircuitInfo.get(CircuitInfo.name == name)
    sim_result = SimResult.get(SimResult.circuit == circuit,
                               SimResult.dir_idx == dir_idx, SimResult.file_idx == file_idx)

    labels = circuit.labels
    input_size = circuit.input_size
    sim_file_name = composite_file_name(name, dir_idx, file_idx, ".sim")

    #truth table is computed in c++ extension code and has been sorted
    truth_table = generate_truth_from_sim_imp(sim_file_name, input_size)

    #compute logic expression for each output index
    output_idx = range(len(labels))
    output_idx = output_idx[input_size:]

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
        target_circuit = CircuitInfo.get(CircuitInfo.name == name)
        target_result = SimResult.get(SimResult.circuit == target_circuit,
                                      SimResult.dir_idx == 0, SimResult.file_idx == 0)
        is_correct = set(target_result.truth_table) == set(truth_table)


    #save the computed result into database
    sim_result.truth_table = truth_table
    sim_result.logic_expr = logic_expr
    sim_result.is_correct = is_correct
    sim_result.save()


def simulate_circuit(name, dir_idx, file_idx):
    generate_qca_and_sim_from_structure(name, dir_idx, file_idx)
    generate_truth_and_logic_from_sim(name, dir_idx, file_idx)


def simulate_benchmark(benchmark_file_name):
    load_benchmark(benchmark_file_name)
    name = os.path.basename(benchmark_file_name)
    name = name[:name.find(".")]

    circuit = CircuitInfo.get(CircuitInfo.name == name)
    size = circuit.normal_size

    threads = []
    n_frac = math.factorial(size)
    for dir_idx in range(size+1):
        m_frac = math.factorial(dir_idx)
        n_m_frac = math.factorial(size - dir_idx)
        tmp = n_frac // (m_frac * n_m_frac)

        # for file_idx in range(tmp):
        #     simulate_circuit(name, dir_idx, file_idx)
        for file_idx in range(tmp):
            threads.append(threading.Thread(target=simulate_circuit, args=(name, dir_idx, file_idx)))

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()


def create_tables():
    db.connect()
    db.create_tables([CircuitInfo, SimResult], safe=True)


parser = argparse.ArgumentParser(description="Specify the benchmark file path")
parser.add_argument("-i", type=str, nargs='?', dest='benchmark_file_name', help='benchmark file name')

if __name__ == "__main__":
    args = parser.parse_args()

    create_tables()

    simulate_benchmark(args.benchmark_file_name)

    name = os.path.basename(args.benchmark_file_name)
    name = name[:name.find(".")]
    circuit = CircuitInfo.get(CircuitInfo.name == name)

    statistics_file_name = composite_file_name(name)
    statistics_file_name = os.path.join(statistics_file_name, ".statistics")

    statistics_file = open(statistics_file_name, "w")

    size = circuit.normal_size
    for dir_idx in range(size):
        sim = SimResult.select(fn.Count().alias("total_count"))\
            .where(SimResult.circuit == circuit, SimResult.dir_idx == dir_idx).get()
        total_count = sim.total_count

        sim = SimResult.select(fn.Count().alias("error_count")) \
            .where(SimResult.circuit == circuit, SimResult.dir_idx == dir_idx, SimResult.is_correct == False).get()
        error_count = sim.error_count

        statistics_file.write("Missing Pattern : {0}\n".format(dir_idx))
        statistics_file.write("Total Number : {0}\n".format(total_count))
        statistics_file.write("Error Number : {0}\n".format(error_count))
        statistics_file.write("Error Rate : {0}\n".format(error_count/total_count))
        statistics_file.write("\n")

        for sim in SimResult.select(SimResult.logic_expr, fn.Count().alias("count"))\
                .where(SimResult.circuit == circuit, SimResult.dir_idx == dir_idx).group_by(SimResult.logic_expr):
            logic_expr, count = sim.logic_expr, sim.count

            statistics_file.write("Logic exprssion {0} occured {1} times.\n".format(logic_expr, count))

            statistics_file.write("The qca file names for them are as follows :\n")
            for s in SimResult.select(SimResult.qca_file_path) \
                    .where(SimResult.circuit == circuit, SimResult.dir_idx == dir_idx, SimResult.logic_expr == str(logic_expr)):
                statistics_file.write(s.qca_file_path)
                statistics_file.write("\n")
        statistics_file.write("\n========================================================================\n\n")

