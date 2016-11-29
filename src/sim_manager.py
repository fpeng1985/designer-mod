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
import itertools
import threading
from functools import reduce
from pyparsing import Literal, OneOrMore, Word, alphanums, nums, alphas, Optional, oneOf, CaselessLiteral, Combine, Group


###############################################################################

parser = argparse.ArgumentParser(description="Specify the benchmark file")
parser.add_argument("-i", type=str, nargs='?', dest='benchmark_file_name', default=r"C:\msys64\common\benchmark\qcasim\majority_gate_1.txt", help='benchmark file name')
parser.add_argument("-o", type=str, nargs='?', dest='output_dir', default=r"C:\Users\fpeng\Documents\sim_manager", help='output file directory')

###############################################################################

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
        
###############################################################################

class TraceParser:
    #data
    trace_container = []
    
    #grammar
    trace_data_item = Combine(Optional(Literal("-")) + Word(nums) + Literal(".") + Word(nums) + CaselessLiteral("e") +
                              oneOf("+ -") + Word(nums)).setParseAction(lambda tok: float(tok[0]))
    
    trace_data = Literal("[TRACE_DATA]").suppress() + OneOrMore(trace_data_item) + Literal("[#TRACE_DATA]").suppress()
    
    data_labels = Literal("data_labels=").suppress() + (Word(alphanums) + Optional(Word(nums))).setParseAction(lambda tok: reduce(lambda x, y: x + " " + y, tok))
    trace_function = Literal("trace_function=").suppress() + Word(nums).setParseAction(lambda tok: int(tok[0]))
    drawtrace = Literal("drawtrace=").suppress() + Word(alphas)
    
    trace = Literal("[TRACE]").suppress() + data_labels("data_labels") + trace_function("trace_function") + \
            drawtrace.suppress() + Group(trace_data)("trace_data") + Literal("[#TRACE]").suppress()
    
    traces = Literal("[TRACES]").suppress() + OneOrMore(Group(trace)).setParseAction(
        lambda tok: TraceParser.trace_container.extend( [(tok[i].data_labels[0], tok[i].trace_data.asList()) for i in range(len(tok))] )
        ) + Literal("[#TRACES]").suppress()
    
    clocks = Literal("[CLOCKS]").suppress() + OneOrMore(Group(trace)) + Literal("[#CLOCKS]").suppress()
    
    number_samples = Literal("number_samples=").suppress() + Word(nums)("number_samples").setParseAction(lambda tok: int(tok[0]))
    number_of_traces = Literal("number_of_traces=").suppress() + Word(nums)("number_of_traces").setParseAction(lambda tok: int(tok[0]))
    simulation_data = Literal("[SIMULATION_DATA]").suppress() + number_samples + number_of_traces + traces + clocks + Literal("[#SIMULATION_DATA]").suppress()
    
    simulation_output = Literal("[SIMULATION_OUTPUT]").suppress() + simulation_data + \
                        Literal("[TYPE:BUS_LAYOUT]").suppress() + Literal("[#TYPE:BUS_LAYOUT]").suppress() + \
                        Literal("[#SIMULATION_OUTPUT]").suppress()
    
    def generate_truth_table_file_from_sim(sim_file_name):
        print("generating truth table file for {0}".format(sim_file_name))
        
        TraceParser.trace_container.clear()
        TraceParser.simulation_output.parseFile(sim_file_name)
       
        labels = []
        trace_datas = []
        for trace in TraceParser.trace_container:
            labels.append(trace[0])
            trace_datas.append(trace[1])
    
        data = []
        for i in range(len(trace_datas[0])):
            tmp = []
            for j in range(len(trace_datas)):
                tmp.append(trace_datas[j][i])
            data.append(tuple(tmp))
    
        output_index = []
        for i in range(len(labels)):
            if labels[i].startswith("O"):
                output_index.append(i)
        # print(output_index)
    
        truth = set()
        for d in data:
            flag = True
            for i in output_index:
                if -0.5<d[i]<0.5:
                   flag = False
            if flag:
                tmp = [ int(x) for x in d[:output_index[0]] ]
                for i in output_index:
                    if d[i] > 0.5:
                        tmp.append(1)
                    else:
                        tmp.append(-1)
                truth.add(tuple(tmp))
    
        base_name = os.path.basename(sim_file_name)
        base_name = base_name[:base_name.find(".")]
        output_dir = os.path.dirname(sim_file_name)
        output_file_name = os.path.join(output_dir, base_name+".truth")
        with open(output_file_name, 'w') as outf:
            for label in labels:
                outf.write("{0}\t".format(label))
            outf.write("\n==========================================\n")
            for t in truth:
                for d in t:
                    outf.write("{0}\t".format(d))
                outf.write("\n")

###############################################################################

def generate_qca_and_sim_file_from_structure(structure_file_name):
    input_file_name = os.path.abspath(structure_file_name)
    output_dir = os.path.abspath(os.path.dirname(structure_file_name))

    print("generating qca and sim file for circuit structure {0}".format(input_file_name))
    subprocess.call("pfmain -i {0} -o {1}".format(input_file_name, output_dir), shell=True)

if __name__ == "__main__":
    args = parser.parse_args()

    print(args.benchmark_file_name)
    print(args.output_dir)
    base_name = os.path.basename(args.benchmark_file_name)
    base_name = base_name[:base_name.find(".")]

    outdir = os.path.join(args.output_dir, base_name)
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    circuit, normals = load_structure_file(args.benchmark_file_name)
    
    threads = []
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
            #print("processing {0}".format(os.path.abspath(structure_file_name)))
            #subprocess.call("pfmain -i {0} -o {1}".format(os.path.abspath(structure_file_name), os.path.abspath(resultdir)), shell=True)
            t = threading.Thread(target=generate_qca_and_sim_file_from_structure, args=(structure_file_name,)).start()
            threads.append(t)
    for t in threads:
        #t.join()
        pass
    
    dir_names = os.listdir(outdir)
    for dir_name in dir_names:
        output_dir = os.path.join(outdir, dir_name)
        circuit_files = os.listdir(output_dir)
        sim_files = filter(lambda x: x.endswith(".sim"), circuit_files)
        sim_file_names = [os.path.join(output_dir, sim_file) for sim_file in sim_files]
        for sim_file_name in sim_file_names:
            TraceParser.generate_truth_table_file_from_sim(os.path.abspath(sim_file_name))
    
