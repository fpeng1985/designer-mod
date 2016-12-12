# -*- coding: utf-8 -*-

import copy
import fileinput
import itertools
import math
import multiprocessing
import os
import subprocess
import shutil

from bsddb3 import db
# from peewee import *
import qm

from generate_qca_and_sim_from_structure_imp import generate_qca_and_sim_from_structure_imp
from generate_truth_from_sim_imp import generate_truth_from_sim_imp

from config import outdir


# class ListField(Field):
#     db_field = 'list'
#
#     def db_value(self, value):
#         return str(value)
#
#     def python_value(self, value):
#         return eval(value)
#
#
# SqliteDatabase.register_fields({'list': 'list'})
#
#
# class BaseModel(Model):
#     class Meta:
#         database = sqlite3_db
#
#
# class CircuitInfo(BaseModel):
#     name = CharField(unique=True)
#     input_size = IntegerField(default=0)
#     output_size = IntegerField(default=0)
#     normal_size = IntegerField(default=0)
#     labels = ListField(default=[])
#
#
# class SimResult(BaseModel):
#     circuit = ForeignKeyField(CircuitInfo, related_name="sim_results")
#     dir_idx = IntegerField(default=0)
#     file_idx = IntegerField(default=0)
#     structure = ListField(default=[])
#     missing_indices = ListField(default=[])
#     qca_file_path = CharField(default="")
#     sim_file_path = CharField(default="")
#     truth_table = ListField(default=[])
#     logic_expr = ListField(default=[])
#     is_correct = BooleanField(default=True)
#
#
# def create_tables():
#     sqlite3_db.connect()
#     sqlite3_db.create_tables([CircuitInfo, SimResult], safe=True)


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


class QCADB:
    def __init__(self, outdir, design_name):
        if not os.path.exists(outdir):
            os.mkdir(outdir)

        self.dbdir = os.path.join(outdir, design_name)
        if os.path.exists(self.dbdir):
            shutil.rmtree(self.dbdir)
        os.mkdir(self.dbdir)

        self.design_name = design_name

        self.filename = "qca.db"
        self.dbenv = db.DBEnv()
        self.dbenv.open(self.dbdir, db.DB_CREATE | db.DB_INIT_MPOOL | db.DB_INIT_LOCK | db.DB_INIT_LOG | db.DB_INIT_TXN)

    def _create_table(self, dbname, dbvalues):
        print(dbname)
        txn = self.dbenv.txn_begin(flags=db.DB_TXN_BULK)
        cur_db = db.DB(self.dbenv)
        cur_db.open(self.filename, dbname=dbname, dbtype=db.DB_BTREE, flags=db.DB_CREATE, txn=txn)

        #kio = io.BytesIO()
        #vio = io.BytesIO()

        for key, value in dbvalues.items():
            #pickle.dump(key, kio)
            #pickle.dump(value, vio)
            #cur_db.put(kio.getvalue(), vio.getvalue(), txn)
            k = key.encode()
            v = str(value).encode()
            cur_db.put(k, v, txn=txn)

        txn.commit()
        cur_db.close()

    def load_benchmark(self, benchmark_file_name):
        name = os.path.basename(benchmark_file_name)
        name = name[:name.find(".")]

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

        self._create_table("circuit", {"input_size": input_size, "output_size": output_size, "normal_size": normal_size,
                                       "labels": labels})

        pool = multiprocessing.Pool(processes=4)
        for dir_idx in range(normal_size+1):
            os.mkdir(composite_file_name(name, dir_idx))

            combinations = itertools.combinations(normals, dir_idx)
            file_idx = 0
            for comb in combinations:
                cur_structure = copy.deepcopy(structure)
                for r, c in comb:
                    cur_structure[r][c] = 0

                print(dir_idx, file_idx)
                pool.apply_async(self._create_table, args=("_".join([str(dir_idx), str(file_idx)]),
                                                     {"structure": cur_structure, "missing_indices": comb}))
                file_idx += 1

        pool.close()
        pool.join()

    def generate_qca_and_sim_from_structure(self, dir_idx, file_idx):
        txn = self.dbenv.txn_begin(flags=db.DB_TXN_BULK)
        cur_db = db.DB(self.dbenv)
        cur_db.open(self.filename, dbname="_".join([str(dir_idx), str(file_idx)]), txn=txn)

        #kio = io.BytesIO()
        #vio = io.BytesIO()

        #pickle.dump("structure", kio)
        #structure = pickle.loads(cur_db.get(kio.getvalue(), txn=txn))
        structure = eval(cur_db.get("structure".encode(), txn=txn))
        print(structure)

        qca_file_name = composite_file_name(self.design_name, dir_idx, file_idx, ".qca")
        sim_file_name = composite_file_name(self.design_name, dir_idx, file_idx, ".sim")

        generate_qca_and_sim_from_structure_imp(structure, qca_file_name, sim_file_name)

        #update database
        #pickle.dump("qca_file_path", kio)
        #pickle.dump(qca_file_path, vio)
        #cur_db.put(kio.getvalue(), vio.getvalue(), txn)

        #pickle.dump("sim_file_path", kio)
        #pickle.dump(sim_file_path, vio)
        #cur_db.put(kio.getvalue(), vio.getvalue(), txn)

        cur_db.put("dir_idx".encode(), str(dir_idx).encode(), txn=txn)
        cur_db.put("file_idx".encode(), str(file_idx).encode(), txn=txn)
        cur_db.put("qca_file_path".encode(), str(qca_file_path).encode(), txn=txn)
        cur_db.put("sim_file_path".encode(), str(sim_file_path).encode(), txn=txn)


        txn.commit()
        cur_db.close()

    def generate_truth_and_logic_from_sim(self, dir_idx, file_idx):
        txn = self.dbenv.txn_begin(flags=db.DB_TXN_BULK)
        cur_db = db.DB(self.dbenv)
        cur_db.open(self.filename, dbname="_".join([str(dir_idx), str(file_idx)]), txn=txn)

        #kio = io.BytesIO()
        #vio = io.BytesIO()

        #pickle.dump("labels", kio)
        #labels = pickle.loads(cur_db.get(kio.getvalue(), txn=txn))
        labels = eval(cur_db.get("labels".encode(), txn=txn))
        print(labels)

        #pickle.dump("input_size", kio)
        #input_size = pickle.loads(cur_db.get(kio.getvalue(), txn=txn))
        input_size = eval(cur_db.get("input_size".encode(), txn=txn))

        sim_file_name = composite_file_name(self.design_name, dir_idx, file_idx, ".sim")

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
            target_db = db.DB(self.dbenv)
            target_db.open(self.filename, dbname="0_0", txn=txn)

            #pickle.dump("truth_table", kio)
            #target_truth_table = pickle.loads(target_db.get(kio.getvalue(), txn=txn))
            target_truth_table = eval(cur_db.get("truth_table".encode(), txn=txn))

            is_correct = set(target_truth_table) == set(truth_table)
            #target_db.close()

        #save the computed result into database
        #pickle.dump("truth_table", kio)
        #pickle.dump(truth_table, vio)
        #cur_db.put(kio.getvalue(), vio.getvalue(), txn=txn)

        #pickle.dump("logic_expr", kio)
        #pickle.dump(logic_expr, vio)
        #cur_db.put(kio.getvalue(), vio.getvalue(), txn=txn)

        #pickle.dump("is_correct", kio)
        #pickle.dump(is_correct, vio)
        #cur_db.put(kio.getvalue(), vio.getvalue(), txn=txn)

        cur_db.put("truth_table".encode(), str(truth_table).encode(), txn=txn)
        cur_db.put("logic_expr".encode(), str(logic_expr).encode(), txn=txn)
        cur_db.put("is_correct".encode(), str(is_correct).encode(), txn=txn)

        txn.commit()
        cur_db.close()

    def simulate_circuit(self, dir_idx, file_idx):
        self.generate_qca_and_sim_from_structure(dir_idx, file_idx)
        self.generate_truth_and_logic_from_sim(dir_idx, file_idx)
        print("{0}_{1} finished".format(dir_idx, file_idx))

    def simulate_benchmark(self, benchmark_file_name):
        self.load_benchmark(benchmark_file_name)

        txn = self.dbenv.txn_begin(flags=db.DB_TXN_BULK)
        cur_db = db.DB(self.dbenv)
        cur_db.open(self.filename, dbname="circuit", txn=txn)

        #kio = io.BytesIO()
        #vio = io.BytesIO()

        #pickle.dump("normal_size", kio)
        #normal_size = pickle.loads(cur_db.get(kio.getvalue(), txn=txn))
        normal_size = eval(cur_db.get("normal_size".encode(), txn=txn))
        txn.commit()

        pool = multiprocessing.Pool(processes=4)
        n_frac = math.factorial(normal_size)
        for dir_idx in range(normal_size+1):
            m_frac = math.factorial(dir_idx)
            n_m_frac = math.factorial(normal_size - dir_idx)
            tmp = n_frac // (m_frac * n_m_frac)

            for file_idx in range(tmp):
                pool.apply_async(self.simulate_circuit, args=(dir_idx, file_idx))
        pool.close()
        pool.join()

    def generate_statistic(self):
        txn = self.dbenv.txn_begin(flags=db.DB_TXN_BULK)
        circuit_db = db.DB(self.dbenv)
        circuit_db.open(self.filename, dbname="circuit", txn=txn)

        normal_size = eval(circuit_db.get("normal_size".encode(), txn=txn))

        with open(os.path.join(outdir, self.design_name+"statistics"), "w") as statistics_file:
            n_frac = math.factorial(normal_size)
            for dir_idx in range(normal_size+1):
                total_count = 0
                error_count = 0
                logic_exprs = {}

                m_frac = math.factorial(dir_idx)
                n_m_frac = math.factorial(normal_size - dir_idx)
                tmp = n_frac // (m_frac * n_m_frac)

                for file_idx in range(tmp):
                    cur_db = db.DB(self.dbenv)
                    print("hello", dir_idx, file_idx)
                    cur_db.open(self.filename, dbname="_".join([str(dir_idx), str(file_idx)]), txn=txn)

                    total_count += 1
                    is_correct = eval(cur_db.get("is_correct".encode(), txn=txn))
                    if not is_correct:
                        error_count += 1

                    logic_expr = eval(cur_db.get("logic_expr".encode(), txn=txn))
                    qca_file_path = eval(cur_db.get("qca_file_path".encode(), txn=txn))
                    if logic_expr in logic_exprs:
                        logic_exprs[logic_expr].append(qca_file_path)
                    else:
                        logic_exprs[logic_expr] = [qca_file_path]

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




# if __name__ == "__main__":
#     db.connect()
#     db.create_tables([CircuitInfo, SimResult], safe=True)
#
#     structure = [
#         [0,  0,  1,  0,  0],
#         [0,  1,  1,  1,  0],
#         [-1, 1,  1,  1, -2],
#         [0,  1,  1,  1,  0],
#         [0,  0,  1,  0,  0]
#     ]
#
#     circuit_info = CircuitInfo.create(name='majority_gate', input_size=3, output_size=1,
#                                       labels=['I02', 'I20', 'I42', 'O24'])
#     circuit_info.save()
#
#     sim_result = SimResult.create(circuit=circuit_info, dir_idx=1, file_idx=1, structure=structure)
#     sim_result.save()
#
#     for circuit in CircuitInfo.select():
#         print(circuit.name)
#         print(circuit.labels)
#
#     for sim in SimResult.select():
#         print(sim.structure)
#         print(sim.truth_table)
#         print(sim.is_correct)

if __name__ == "__main__":
    qcadb = QCADB("./output", "majority_gate_1")
    qcadb.simulate_benchmark("/home/fpeng/Workspace/designer-mod/qcamod/benchmark/majority_gate_1.txt")
    qcadb.generate_statistic()
