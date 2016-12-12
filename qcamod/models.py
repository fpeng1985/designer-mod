# -*- coding: utf-8 -*-


# from peewee import *
# from config import db
#
#
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
#         database = db
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

from bsddb3 import db
import os
import shutil
import pickle
import io
import fileinput
import itertools
import copy
import multiprocessing


def composite_file_name(circuit_name, dir_idx=None, file_idx=None, appendix=None):
    path = os.path.join(outdir, circuit_name)
    if dir_idx is not None:
        path = os.path.join(path, str(dir_idx))
        if file_idx is not None:
            path = os.path.join(path, str(file_idx) + appendix)
    return os.path.normpath(os.path.abspath(path))


class QCADB:
    envflags = db.DB_CREATE | db.DB_INIT_MPOOL | db.DB_INIT_LOCK | db.DB_INIT_LOG | db.DB_INIT_TXN

    def __init__(self, outdir, design_name):
        if not os.path.exists(outdir):
            os.mkdir(outdir)

        self.dbdir = os.path.join(outdir, design_name)
        if os.path.exists(self.dbdir):
            shutil.rmtree(self.dbdir)
        os.mkdir(self.dbdir)

        self.filename = "qca.db"
        self.dbenv = db.DBEnv()
        self.dbenv.open(self.dbdir, QCADB.envflags)

    def _create_table(self, dbname, dbvalues):
        txn = self.dbenv.txn_begin(flags=db.DB_TXN_BULK)
        cur_db = db.DB(self.dbenv)
        cur_db.open(self.filename, dbname=dbname, dbtype=db.DB_BTREE, flags=db.DB_CREATE, txn=txn)

        kio = io.BytesIO()
        vio = io.BytesIO()

        for key,value in dbvalues.items():
            pickle.dump(key, kio)
            pickle.dump(value, vio)
            cur_db.put(kio.getvalue(), vio.getvalue(), txn)

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

        for dir_idx in range(normal_size+1):
            os.mkdir(composite_file_name(name, dir_idx))

            combinations = itertools.combinations(normals, dir_idx)
            file_idx = 0
            for comb in combinations:
                cur_structure = copy.deepcopy(structure)
                for r, c in comb:
                    cur_structure[r][c] = 0

                print("_".join([str(dir_idx), str(file_idx)]))

                self._create_table("_".join([str(dir_idx), str(file_idx)]), {"structure": cur_structure,
                                                                             "missing_indices": comb})

                file_idx += 1


if __name__ == "__main__":
    qcadb = QCADB(r".\output", "majority_gate_1")
    qcadb.load_benchmark(r"C:\Users\fpeng\Data\Workspace\HFUT\designer-mod\qcamod\benchmark\majority_gate_1.txt")
