# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import argparse
import fileinput
import os
import copy
import subprocess

parser = argparse.ArgumentParser(description="Specify the benchmark file")
parser.add_argument("-i", type=str, nargs='?', dest='benchmark_file_name', help='benchmark file name')
parser.add_argument("-w", type=str, nargs='?', dest='output_dir', help='output file directory')


def _combine(a, n, b, m, M, combinations):
    for i in range(n, m - 1, -1):
        b[m - 1] = i - 1
        if m > 1:
            _combine(a, i - 1, b, m - 1, M, combinations)
        else:
            tmp = []
            for j in range(M - 1, -1, -1):
                tmp.append(a[b[j]])
            combinations.append(tmp)


def combine(a, m, combinations):
    assert (1 <= m <= len(a))
    # assert (m >= 1 and m <= len(a))
    assert (len(combinations) == 0)

    b = [0] * m
    _combine(a, len(a), b, m, m, combinations)


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


if __name__ == "__main__":
    args = parser.parse_args()

    base_name = os.path.basename(args.benchmark_file_name)
    base_name = base_name[:base_name.find(".")]

    outdir = os.path.join(args.output_dir, base_name)
    if not os.path.exists(outdir):
        os.mkdir(outdir)
    print(outdir)

    circuit, normals = load_structure_file(args.benchmark_file_name)

    for i in range(len(normals)):
        resultdir = os.path.join(outdir, str(i+1))
        if not os.path.exists(resultdir):
            os.mkdir(resultdir)

        combinations = []
        combine(normals, i+1, combinations)

        cnt = 1
        for comb in combinations:
            structure = copy.deepcopy(circuit)
            for r, c in comb:
                structure[r][c] = 0
            structure_file_name = os.path.join(resultdir, str(cnt)+".txt")
            write_structure_file(structure, structure_file_name)
            cnt += 1
            print("processing {0}".format(os.path.abspath(structure_file_name)))
            subprocess.call("pfmain -i {0} -o {1}".format(os.path.abspath(structure_file_name), os.path.abspath(resultdir)), shell=True)
