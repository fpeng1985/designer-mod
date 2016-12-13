# -*- coding: utf-8 -*-

import copy
import fileinput
import itertools
import multiprocessing
import os
import shutil
import time

from peewee import *
import qm

from generate_qca_and_sim_from_structure_imp import generate_qca_and_sim_from_structure_imp
from generate_truth_from_sim_imp import generate_truth_from_sim_imp

from config import *


########################################################################################
#######################SimResult database schema definition#############################
########################################################################################

class ListField(Field):
    db_field = 'list'

    def db_value(self, value):
        return str(value)

    def python_value(self, value):
        return eval(value)

SqliteDatabase.register_fields({'list': 'list'})


class SimResult(Model):
    class Meta:
        database = DB

    name = CharField(default="")
    dir_idx = IntegerField(default=0)
    file_idx = IntegerField(default=0)
    structure = ListField(default=[])
    missing_indices = ListField(default=[])
    qca_file_path = CharField(default="")
    sim_file_path = CharField(default="")
    truth_table = ListField(default=[])
    logic_expr = ListField(default=[])
    is_correct = BooleanField(default=True)


def create_tables():
    DB.connect()
    DB.create_tables([SimResult], safe=True)


########################################################################################
#####################################decorator##########################################
########################################################################################

def print_timing(func):
    def wrapper(*arg):
        t1 = time.time()
        res = func(*arg)
        t2 = time.time()
        print('%s took %0.3f ms' % (getattr(func, '__name__'), (t2-t1)*1000.0))
        return res
    return wrapper


########################################################################################
##################################helper functions######################################
########################################################################################


def composite_file_name(circuit_name, dir_idx=None, file_idx=None, appendix=None):
    path = os.path.join(OUT_DIR, circuit_name)
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


########################################################################################
##################################main functions########################################
########################################################################################


@print_timing
def load_benchmark(benchmark_file_name):
    assert(os.path.exists(benchmark_file_name))
    design_name = os.path.basename(benchmark_file_name)
    design_name = design_name[:design_name.find(".")]

    #clean the output directory
    if not os.path.exists(OUT_DIR):
        os.mkdir(OUT_DIR)

    dbdir = os.path.join(OUT_DIR, design_name)
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

    #simulate the original circuit structure
    benchmark_output_dir = composite_file_name(dbdir, 0)
    if not os.path.exists(benchmark_output_dir):
        os.mkdir(benchmark_output_dir)

    qca_file_name = composite_file_name(design_name, 0, 0, ".qca")
    sim_file_name = composite_file_name(design_name, 0, 0, ".sim")

    generate_qca_and_sim_from_structure_imp(structure, qca_file_name, sim_file_name)
    truth_table = generate_truth_from_sim_imp(sim_file_name, input_size)

    output_idx = range(len(labels))[input_size:]

    logic_expr = []
    for out_idx in output_idx:
        truth_values = []
        for t in truth_table:
            truth_values.append(t[:input_size] + (t[out_idx],))

        expr = compute_logic_expression_from_truth_table(labels[:input_size] + [labels[out_idx]],
                                                         truth_values)
        logic_expr.append(expr)

    #save the circuit infos
    circuit_info = dict(
        name=design_name, input_size=input_size, output_size=output_size, normal_size=normal_size,
        labels=labels, structure=structure, qca_file_path=qca_file_name, sim_file_path=sim_file_name,
        truth_table=truth_table, logic_expr=logic_expr
    )

    #populate the args_list for all the other structures
    args_list = []
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
            args_list.append({"name": design_name, "dir_idx": dir_idx, "file_idx": file_idx,
                              "structure": cur_structure, "missing_indices": comb})
            file_idx += 1

    #create sqlite3 database
    create_tables()

    return circuit_info, args_list


def simulate_circuit(circuit_info, args):
    assert(isinstance(circuit_info, dict))
    assert(isinstance(args, dict))

    #prepare data used in generate_qca_and_sim_from_structure_imp
    design_name = circuit_info["name"]

    dir_idx = args["dir_idx"]
    file_idx = args["file_idx"]

    qca_file_name = composite_file_name(design_name, dir_idx, file_idx, ".qca")
    sim_file_name = composite_file_name(design_name, dir_idx, file_idx, ".sim")

    structure = args["structure"]

    #generate qca and sim file
    generate_qca_and_sim_from_structure_imp(structure, qca_file_name, sim_file_name)

    #truth table is computed in c++ extension code and has been sorted
    input_size = circuit_info["input_size"]
    truth_table = generate_truth_from_sim_imp(sim_file_name, input_size)

    #compute logic expression for each output index
    labels = circuit_info["labels"]
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
    is_correct = set(circuit_info["truth_table"]) == set(truth_table)

    #save the computed result and return its value
    args["qca_file_path"] = qca_file_name
    args["sim_file_path"] = sim_file_name
    args["truth_table"] = truth_table
    args["logic_expr"] = logic_expr
    args["is_correct"] = is_correct
    return args


class ManagedArgsUpdater:
    def __init__(self, lst, lock):
        self.lst = lst
        self.lock = lock

    def __call__(self, args):
        with self.lock:
            self.lst.append(args)


@print_timing
def simulate_benchmark(circuit_info, args_list):
    pool = multiprocessing.Pool(processes=PROCESS_NUM)

    ret_list = pool.starmap(simulate_circuit, zip([circuit_info for i in range(len(args_list))], args_list))
    pool.close()
    pool.join()

    for args in ret_list:
        SimResult.create(**args)


@print_timing
def generate_statistics(circuit_info):
    name = circuit_info["name"]
    statistics_file_name = composite_file_name(name)
    statistics_file_name = os.path.join(statistics_file_name, name+".statistics")

    statistics_file = open(statistics_file_name, "w")

    size = circuit_info["normal_size"]
    for dir_idx in range(1, size+1):
        sim = SimResult.select(fn.Count().alias("total_count")) \
            .where(SimResult.name == name, SimResult.dir_idx == dir_idx).get()
        total_count = sim.total_count

        sim = SimResult.select(fn.Count().alias("error_count")) \
            .where(SimResult.name == name, SimResult.dir_idx == dir_idx, SimResult.is_correct == False).get()
        error_count = sim.error_count

        statistics_file.write("Missing Pattern : {0}\n".format(dir_idx))
        statistics_file.write("Total Number : {0}\n".format(total_count))
        statistics_file.write("Error Number : {0}\n".format(error_count))
        statistics_file.write("Error Rate : {0}\n".format(error_count/total_count))
        statistics_file.write("\n")

        for sim in SimResult.select(SimResult.logic_expr, fn.Count().alias("count")) \
                .where(SimResult.name == name, SimResult.dir_idx == dir_idx).group_by(SimResult.logic_expr):
            logic_expr, count = sim.logic_expr, sim.count

            statistics_file.write("Logic exprssion {0} occured {1} times.\n".format(logic_expr, count))

            statistics_file.write("The qca file names for them are as follows :\n")
            for s in SimResult.select(SimResult.qca_file_path).where(SimResult.name == name,
                                                                     SimResult.dir_idx == dir_idx,
                                                                     SimResult.logic_expr == str(logic_expr)):
                statistics_file.write(s.qca_file_path)
                statistics_file.write("\n")
        statistics_file.write("\n========================================================================\n\n")


if __name__ == "__main__":
    benchmark_file_name = "/home/fpeng/Workspace/designer-mod/qcamod/benchmark/majority_gate_1.txt"

    circuit_info, args_list = load_benchmark(benchmark_file_name)
    simulate_benchmark(circuit_info, args_list)
    generate_statistics(circuit_info)
