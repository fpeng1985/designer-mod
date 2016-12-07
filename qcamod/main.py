# -*- coding: utf-8 -*-

from app import *
from models import *

import os
import fileinput
import itertools
import copy
import shutil

from generate_qca_and_sim_from_structure_imp import generate_qca_and_sim_from_structure_imp


def composite_file_name(circuit_name, dir_idx=None, file_idx=None, appendix=None):
    path = os.path.join(outdir, circuit_name)
    if dir_idx is not None:
        path = os.path.join(path, str(dir_idx))
        if file_idx is not None:
            path = os.path.join(path, str(file_idx) + appendix)
    return os.path.normpath(os.path.abspath(path))


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

    labels.sort()

    circuit = CircuitInfo.create(name=name, input_size=input_size, output_size=output_size, labels=labels)
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
            sim_result = SimResult.create(circuit=circuit, dir_idx=dir_idx, file_idx=file_idx,
                                          structure=cur_structure, missing_indices=comb)
            sim_result.save()

            file_idx += 1


def generate_qca_and_sim_from_structure(name, dir_idx, file_idx):
    circuit = CircuitInfo.get(CircuitInfo.name == name)
    sim_result = SimResult.get(SimResult.circuit == circuit,
                               SimResult.dir_idx == dir_idx, SimResult.file_idx == file_idx)

    structure = sim_result.structure
    output_dir_name = composite_file_name(name, dir_idx)

    generate_qca_and_sim_from_structure_imp(structure, output_dir_name, name)


def create_tables():
    db.connect()
    db.create_tables([CircuitInfo, SimResult], safe=True)


if __name__ == "__main__":
    create_tables()
    load_benchmark(r"C:\Users\fpeng\Data\Workspace\HFUT\designer-mod\qcamod\benchmark\majority_gate_1.txt")
    generate_qca_and_sim_from_structure("majority_gate_1", 0, 0)
    for circuit in CircuitInfo.select():
        print(circuit.name)

