# -*- coding: utf-8 -*-

import os
import qm
from functools import reduce
from pyparsing import Literal, OneOrMore, Word, alphanums, nums, alphas, Optional, oneOf, CaselessLiteral, Combine, Group


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
    lambda tok: trace_container.extend( [(tok[i].data_labels[0], tok[i].trace_data.asList()) for i in range(len(tok))] )
    ) + Literal("[#TRACES]").suppress()

clocks = Literal("[CLOCKS]").suppress() + OneOrMore(Group(trace)) + Literal("[#CLOCKS]").suppress()

number_samples = Literal("number_samples=").suppress() + Word(nums)("number_samples").setParseAction(lambda tok: int(tok[0]))
number_of_traces = Literal("number_of_traces=").suppress() + Word(nums)("number_of_traces").setParseAction(lambda tok: int(tok[0]))
simulation_data = Literal("[SIMULATION_DATA]").suppress() + number_samples + number_of_traces + traces + clocks + Literal("[#SIMULATION_DATA]").suppress()

simulation_output = Literal("[SIMULATION_OUTPUT]").suppress() + simulation_data + \
                    Literal("[TYPE:BUS_LAYOUT]").suppress() + Literal("[#TYPE:BUS_LAYOUT]").suppress() + \
                    Literal("[#SIMULATION_OUTPUT]").suppress()

                    
#functions
def compute_logic_expression_from_truth_table(labels, truth_values):
    input_size = len(labels)-1
    
    ones = []
    zeros = []
    for t in truth_values:
        tmp_val = 0
        for i in range(input_size):
            tmp_val += t[i]*(2**(input_size-1-i))
        if t[-1] == 1:
            ones.append(tmp_val)
        else:#t[-1] == 0
            zeros.append(tmp_val)
    
    terms = qm.qm(ones=ones, zeros=zeros)
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
                 
    
def generate_truth_and_logic_file_from_sim(sim_file_name):
    print("generating truth table and logic expression file for {0}".format(sim_file_name))
    
    trace_container.clear()
    simulation_output.parseFile(sim_file_name)
   
    #collect data from simulation output file
    labels = []
    trace_datas = []
    for trace in trace_container:
        labels.append(trace[0])
        trace_datas.append(trace[1])

    data = []
    for i in range(len(trace_datas[0])):
        tmp = []
        for j in range(len(trace_datas)):
            tmp.append(trace_datas[j][i])
        data.append(tuple(tmp))

    #compute output index
    output_index = []
    for i in range(len(labels)):
        if labels[i].startswith("O"):
            output_index.append(i)

    #compute truth table
    truth = set()
    for d in data:
        flag = True
        for i in output_index:
            if -0.5<d[i]<0.5:
               flag = False
        if flag:
            tmp = [ int(x) for x in d[:output_index[0]] ]
            tmp = [1 if x==1 else 0 for x in tmp]
            for i in output_index:
                if d[i] > 0.5:
                    tmp.append(1)
                else:
                    tmp.append(0)
            truth.add(tuple(tmp))
    truth_table = list(truth)
    
    #compute logic expression for each output
    logic_exprs = []
    for out_idx in output_index:
        truth_values = []
        for t in truth_table:
            truth_values.append(t[:output_index[0]] + (t[out_idx],))
        
        logic_expr = compute_logic_expression_from_truth_table(labels[:output_index[0]] + [labels[out_idx]], truth_values)
        logic_exprs.append(logic_expr)

    #write truth table and logic expressions to file
    base_name = os.path.basename(sim_file_name)
    base_name = base_name[:base_name.find(".")]
    output_dir = os.path.dirname(sim_file_name)
    output_file_name = os.path.join(output_dir, base_name+".logic")
    with open(output_file_name, 'w') as outf:
        for label in labels:
            outf.write("{0}\t".format(label))
        outf.write("\n")

        for t in truth_table:
            for d in t:
                outf.write("{0}\t".format(d))
            outf.write("\n")
        
        for expr in logic_exprs:
            outf.write(expr)
            outf.write("\n")
    

def generate_logic_files(outdir):
    #print(outdir)
    dir_names = os.listdir(outdir)
    for dir_name in dir_names:
        output_dir = os.path.join(outdir, dir_name)
        circuit_files = os.listdir(output_dir)
        sim_files = filter(lambda x: x.endswith(".sim"), circuit_files)
        sim_file_names = [os.path.join(output_dir, sim_file) for sim_file in sim_files]
        for sim_file_name in sim_file_names:
            generate_truth_and_logic_file_from_sim(os.path.abspath(sim_file_name))
