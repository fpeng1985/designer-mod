# -*- coding: utf-8 -*-

import os
import fileinput
import itertools
import copy

from app import *
from models import *


def composite_file_name(circuit_name, dir_idx, file_idx, appendix):
    path = os.path(outdir)
    path.join(circuit_name)
    path.join(str(dir_idx))
    path.join(str(file_idx) + appendix)
    return os.path.abspath(path)


def load_benchmark(benchmark_file_name):
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

    labels.sort()

    circuit = CircuitInfo.create(name=name, input_size=input_size, output_size=output_size, labels=labels)
    circuit.save()

    for dir_idx in range(normal_size):
        combinations = itertools.combinations(normals, dir_idx)

        for file_idx in range(len(combinations)):
            cur_structure = copy.deepcopy(structure)
            for r, c in combinations[file_idx]:
                cur_structure[r][c] = 0
            cur_normal_size = normal_size - dir_idx
            sim_result = SimResult.create(circuit=circuit, dir_idx=dir_idx, file_idx=file_idx,
                                          missing_indices=combinations[file_idx], structure=cur_structure)
            sim_result.save()


def generate_qca_and_sim_from_structure(name, dir_idx, file_idx):
    circuit = CircuitInfo.get(name == name)
    sim_result = SimResult.get(circuit == circuit, dir_idx == dir_idx, file_idx == file_idx)


def create_tables():
    db.connect()
    db.create_tables([CircuitInfo, SimResult], safe=True)


if __name__ == "__main__":
    create_tables()
