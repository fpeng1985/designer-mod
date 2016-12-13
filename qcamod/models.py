# -*- coding: utf-8 -*-

import copy
import fileinput
import itertools
import math
import multiprocessing
import os
import shutil
import time

from bsddb3 import db
import qm

from generate_qca_and_sim_from_structure_imp import generate_qca_and_sim_from_structure_imp
from generate_truth_from_sim_imp import generate_truth_from_sim_imp

from config import outdir


########################################################################################
##################################helper functions######################################
########################################################################################


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


########################################################################################
##################################db definations########################################
########################################################################################

dbenv = None
design_name = None


def setup_dbenv(dsname):
    global dbenv
    global design_name

    design_name = dsname

    if not os.path.exists(outdir):
        os.mkdir(outdir)

    dbdir = os.path.join(outdir, design_name)
    if os.path.exists(dbdir):
        shutil.rmtree(dbdir)
    os.mkdir(dbdir)

    dbenv = db.DBEnv()
    dbenv.set_tx_max(10000)
    dbenv.open(dbdir, db.DB_CREATE | db.DB_INIT_MPOOL | db.DB_INIT_LOCK |
               db.DB_INIT_LOG | db.DB_INIT_TXN | db.DB_THREAD)


def create_table(dbname, dbvalues):
    # print("Processing %s" % dbname)
    txn = dbenv.txn_begin(flags=db.DB_TXN_BULK)
    cur_db = db.DB(dbenv)
    cur_db.open(filename=dbname, dbtype=db.DB_BTREE, flags=db.DB_CREATE, txn=txn)
    for key, value in dbvalues.items():
        k = key.encode()
        v = str(value).encode()
        cur_db.put(k, v, txn=txn)

    txn.commit()
    cur_db.close()
    # print("Table named %s has been created." % dbname)


@print_timing
def load_benchmark(benchmark_file_name):
    # name = os.path.basename(benchmark_file_name)
    # design_name = name[:name.find(".")]

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

    create_table("circuit", {"input_size": input_size, "output_size": output_size,
                             "normal_size": normal_size, "labels": labels})

    pool = multiprocessing.Pool(processes=10)
    # arg_list = []
    for dir_idx in range(normal_size+1):
        os.mkdir(composite_file_name(design_name, dir_idx))

        combinations = itertools.combinations(normals, dir_idx)
        file_idx = 0
        for comb in combinations:
            cur_structure = copy.deepcopy(structure)
            for r, c in comb:
                cur_structure[r][c] = 0
            # print(dir_idx, file_idx)
            # arg_list.append(("-".join([str(dir_idx), str(file_idx)]), {"structure": cur_structure, "missing_indices": comb}))

            pool.apply(create_table, args=("-".join([str(dir_idx), str(file_idx)]),
                                           {"structure": cur_structure, "missing_indices": comb}))
            file_idx += 1

    # print(arg_list)

    # pool.map(create_table, arg_list)
    pool.close()
    pool.join()
    # print("Create tables done")


def generate_qca_and_sim_from_structure(dir_idx, file_idx):
    txn = dbenv.txn_begin(flags=db.DB_TXN_BULK)
    cur_db = db.DB(dbenv)
    cur_db.open(filename="-".join([str(dir_idx), str(file_idx)]), txn=txn)

    structure = eval(cur_db.get("structure".encode(), txn=txn))
    # print(structure)

    qca_file_name = composite_file_name(design_name, dir_idx, file_idx, ".qca")
    sim_file_name = composite_file_name(design_name, dir_idx, file_idx, ".sim")

    generate_qca_and_sim_from_structure_imp(structure, qca_file_name, sim_file_name)

    #update database
    cur_db.put("dir_idx".encode(), str(dir_idx).encode(), txn=txn)
    cur_db.put("file_idx".encode(), str(file_idx).encode(), txn=txn)
    cur_db.put("qca_file_path".encode(), str(qca_file_name).encode(), txn=txn)
    cur_db.put("sim_file_path".encode(), str(sim_file_name).encode(), txn=txn)

    txn.commit()
    cur_db.close()


def generate_truth_and_logic_from_sim(dir_idx, file_idx):
    txn = dbenv.txn_begin(flags=db.DB_TXN_BULK)

    circuit_db = db.DB(dbenv)
    circuit_db.open(filename="circuit", txn=txn)

    labels = eval(circuit_db.get("labels".encode(), txn=txn))
    input_size = eval(circuit_db.get("input_size".encode(), txn=txn))
    sim_file_name = composite_file_name(design_name, dir_idx, file_idx, ".sim")

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

    cur_db = db.DB(dbenv)
    cur_db.open(filename="-".join([str(dir_idx), str(file_idx)]), txn=txn)

    #compute is_correct
    is_correct = True

    if dir_idx != 0 or file_idx != 0:
        target_db = db.DB(dbenv)
        target_db.open(filename="0-0", txn=txn)
        target_truth_table = eval(target_db.get("truth_table".encode(), txn=txn))
        is_correct = set(target_truth_table) == set(truth_table)
        target_db.close()

    #save the computed result into database
    cur_db.put("truth_table".encode(), str(truth_table).encode(), txn=txn)
    cur_db.put("logic_expr".encode(), str(logic_expr).encode(), txn=txn)
    cur_db.put("is_correct".encode(), str(is_correct).encode(), txn=txn)

    txn.commit()
    circuit_db.close()
    cur_db.close()


def simulate_circuit(dir_idx, file_idx):
    # print("Processing for {0}-{1} begin".format(dir_idx, file_idx))
    generate_qca_and_sim_from_structure(dir_idx, file_idx)
    generate_truth_and_logic_from_sim(dir_idx, file_idx)
    # print("Processing for {0}-{1} finished".format(dir_idx, file_idx))


@print_timing
def simulate_benchmark(benchmark_file_name):
    load_benchmark(benchmark_file_name)
    # print("load benchmark finished")

    txn = dbenv.txn_begin(flags=db.DB_TXN_BULK)
    cur_db = db.DB(dbenv)
    cur_db.open(filename="circuit", txn=txn)

    normal_size = eval(cur_db.get("normal_size".encode(), txn=txn))
    txn.commit()

    pool = multiprocessing.Pool(processes=10)
    n_frac = math.factorial(normal_size)
    for dir_idx in range(normal_size+1):
        m_frac = math.factorial(dir_idx)
        n_m_frac = math.factorial(normal_size - dir_idx)
        tmp = n_frac // (m_frac * n_m_frac)

        for file_idx in range(tmp):
            pool.apply(simulate_circuit, args=(dir_idx, file_idx))
    pool.close()
    pool.join()


def generate_statistics():
    # txn = dbenv.txn_begin()
    circuit_db = db.DB(dbenv)
    circuit_db.open(filename="circuit")

    normal_size = eval(circuit_db.get("normal_size".encode()))

    with open(os.path.join(outdir, design_name+"statistics"), "w") as statistics_file:
        n_frac = math.factorial(normal_size)
        for dir_idx in range(normal_size+1):
            total_count = 0
            error_count = 0
            logic_exprs = {}

            m_frac = math.factorial(dir_idx)
            n_m_frac = math.factorial(normal_size - dir_idx)
            tmp = n_frac // (m_frac * n_m_frac)

            for file_idx in range(tmp):
                cur_db = db.DB(dbenv)
                #print("hello", dir_idx, file_idx)
                cur_db.open(filename="-".join([str(dir_idx), str(file_idx)]))

                total_count += 1
                is_correct = eval(cur_db.get("is_correct".encode()))
                if not is_correct:
                    error_count += 1

                logic_expr = eval(cur_db.get("logic_expr".encode()))
                qca_file_path = (cur_db.get("qca_file_path".encode())).decode()
                for expr in logic_expr:
                    if expr in logic_exprs:
                        logic_exprs[expr].append(qca_file_path)
                    else:
                        logic_exprs[expr] = [qca_file_path]

                statistics_file.write("Missing Pattern : {0}\n".format(dir_idx))
                statistics_file.write("Total Number : {0}\n".format(total_count))
                statistics_file.write("Error Number : {0}\n".format(error_count))
                statistics_file.write("Error Rate : {0}\n".format(error_count/total_count))
                statistics_file.write("\n")

                for logic_expr, qca_file_list in logic_exprs.items():
                    statistics_file.write("Logic exprssion {0} occured {1} times.\n".format(logic_expr,
                                                                                            len(qca_file_list)))
                    statistics_file.write("The qca file names for them are as follows :\n")
                    for qca_file_path in qca_file_list:
                        statistics_file.write(qca_file_path)
                        statistics_file.write("\n")
                statistics_file.write("\n=========================================="
                                      "==============================\n\n")


if __name__ == "__main__":
    print("setup db env")
    setup_dbenv("majority_gate_1")
    simulate_benchmark("/home/fpeng/Workspace/designer-mod/qcamod/benchmark/majority_gate_1.txt")
    generate_statistics()
    print("done")

