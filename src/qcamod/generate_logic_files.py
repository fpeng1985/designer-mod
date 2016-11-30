# -*- coding: utf-8 -*-

import csv
import os
import qm
import subprocess


def generate_truth_from_sim(sim_file_name, output_dir):
    print("generating truth file from {0}".format(sim_file_name))
    subprocess.call("sim_parser -i {0} -o {1}".format(sim_file_name, output_dir), shell=True)

def compute_logic_expression_from_truth_table(labels, truth_values):
    input_size = len(labels)-1
    
    ones = []
    zeros = []
    dc = []
    i = 0
    while (i < len(truth_values)):
        tmp_val = 0
        for j in range(input_size):
            tmp_val += truth_values[i][j]*(2**(input_size-1-j))
        if i < len(truth_values) -1:
            if truth_values[i][:-1]==truth_values[i+1][:-1] and truth_values[i][-1] != truth_values[i+1][-1]:
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
                tmp.append(labels[i] + "'")
        ret.append("*".join(tmp))
    return labels[-1] + " = " + " + ".join(ret)

    
def generate_logic_from_truth(truth_file_name, output_dir):
    #parse labels and truth values
    labels = []
    truth = []
    with open(truth_file_name, 'r') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        labels = reader.fieldnames

        for row in reader:
            tmp = []
            for name in labels:
                tmp.append(int(row[name]))
            truth.append(tuple(tmp))
    truth.sort()
    
    #compute output index
    output_index = []
    for i in range(len(labels)):
        if labels[i].startswith("O"):
            output_index.append(i)
    
    #compute logic expression for each output index
    logic_exprs = []
    for out_idx in output_index:
        truth_values = []
        for t in truth:
            truth_values.append(t[:output_index[0]] + (t[out_idx],))
        
        logic_expr = compute_logic_expression_from_truth_table(labels[:output_index[0]] + [labels[out_idx]], truth_values)
        logic_exprs.append(logic_expr)
        
    #write logic expressions to file
    base_name = os.path.basename(truth_file_name)
    base_name = base_name[:base_name.find(".")]
    
    print("generating logic file from {0}".format(truth_file_name))
    logic_file_name = os.path.abspath(os.path.join(output_dir, base_name+".logic"))
    with open(logic_file_name, 'w') as outf:        
        for expr in logic_exprs:
            outf.write("{0}\n".format(expr))
    

def generate_logic_files(outdir):
    dir_names = os.listdir(outdir)
    for dir_name in dir_names:
        output_dir = os.path.join(outdir, dir_name)
        circuit_files = os.listdir(output_dir)
        sim_files = filter(lambda x: x.endswith(".sim"), circuit_files)
        sim_file_names = [os.path.join(output_dir, sim_file) for sim_file in sim_files]
        for sim_file_name in sim_file_names:
            generate_logic_from_truth(os.path.abspath(sim_file_name), output_dir)


if __name__ == "__main__":
    generate_logic_from_truth(r"C:\Users\fpeng\Documents\sim_manager\majority_gate_1\1\1.truth", r"C:\Users\fpeng\Documents\sim_manager\majority_gate_1\1")