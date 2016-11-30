# -*- coding: utf-8 -*-

import copy
import fileinput
import itertools
import os
import subprocess
import threading


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
        
def generate_qca_and_sim_file_from_structure(structure_file_name):
    input_file_name = os.path.abspath(structure_file_name)
    output_dir = os.path.abspath(os.path.dirname(structure_file_name))

    print("generating qca and sim file for circuit structure {0}".format(input_file_name))
    subprocess.call("qcamod -i {0} -o {1}".format(input_file_name, output_dir), shell=True)
    
    
def generate_simulation_files(benchmark_file_name, outdir):
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
            structure_file_name = os.path.join(output_dir, str(cnt)+".txt")
            write_structure_file(structure, structure_file_name)
            cnt += 1
            #generate qca and sim
            threading.Thread(target=generate_qca_and_sim_file_from_structure, args=(structure_file_name,)).start()
