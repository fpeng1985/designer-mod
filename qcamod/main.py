# -*- coding: utf-8 -*-

from config import *
from models import *

import os
import argparse


parser = argparse.ArgumentParser(description="Specify the benchmark file path")
parser.add_argument("-i", type=str, nargs='?', dest='benchmark_file_name', help='benchmark file name')

if __name__ == "__main__":
    import time
    starttime = time.time()

    args = parser.parse_args()

    create_tables()

    simulate_benchmark(args.benchmark_file_name)

    name = os.path.basename(args.benchmark_file_name)
    name = name[:name.find(".")]
    circuit = CircuitInfo.get(CircuitInfo.name == name)

    statistics_file_name = composite_file_name(name)
    statistics_file_name = os.path.join(statistics_file_name, name)
    statistics_file_name = os.path.join(statistics_file_name, ".statistics")

    statistics_file = open(statistics_file_name, "w")

    size = circuit.normal_size
    for dir_idx in range(size):
        sim = SimResult.select(fn.Count().alias("total_count"))\
            .where(SimResult.circuit == circuit, SimResult.dir_idx == dir_idx).get()
        total_count = sim.total_count

        sim = SimResult.select(fn.Count().alias("error_count")) \
            .where(SimResult.circuit == circuit, SimResult.dir_idx == dir_idx, SimResult.is_correct == False).get()
        error_count = sim.error_count

        statistics_file.write("Missing Pattern : {0}\n".format(dir_idx))
        statistics_file.write("Total Number : {0}\n".format(total_count))
        statistics_file.write("Error Number : {0}\n".format(error_count))
        statistics_file.write("Error Rate : {0}\n".format(error_count/total_count))
        statistics_file.write("\n")

        for sim in SimResult.select(SimResult.logic_expr, fn.Count().alias("count"))\
                .where(SimResult.circuit == circuit, SimResult.dir_idx == dir_idx).group_by(SimResult.logic_expr):
            logic_expr, count = sim.logic_expr, sim.count

            statistics_file.write("Logic exprssion {0} occured {1} times.\n".format(logic_expr, count))

            statistics_file.write("The qca file names for them are as follows :\n")
            for s in SimResult.select(SimResult.qca_file_path) \
                    .where(SimResult.circuit == circuit, SimResult.dir_idx == dir_idx, SimResult.logic_expr == str(logic_expr)):
                statistics_file.write(s.qca_file_path)
                statistics_file.write("\n")
        statistics_file.write("\n========================================================================\n\n")

    endtime = time.time()
    interval = endtime - starttime
    print("Total running time is {0} seconds".format(interval))



