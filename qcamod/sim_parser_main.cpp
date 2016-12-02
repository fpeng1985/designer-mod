#include <string>
#include <iostream>

#include <boost/program_options.hpp>

#include "grammar.hpp"
#include "generate_truth_from_sim.h"


int main(int argc, char *argv[]) {
//    generate_truth_file_from_sim("C:\\Users\\fpeng\\Documents\\sim_manager\\majority_gate_1\\1\\1.sim",
//                                 "C:\\Users\\fpeng\\Documents\\sim_manager\\majority_gate_1\\1");
    using std::cout;
    using std::endl;
    using std::string;

    namespace po = boost::program_options;

    po::options_description desc("Allowed options");
    desc.add_options()
            ("help", "produce help message")
            ("sim-file,i", po::value<string>(), "simulation output file")
            ("out-dir,o", po::value<string>(), "output directory");

    po::variables_map vm;
    po::store(po::parse_command_line(argc, argv, desc), vm);
    po::notify(vm);

    if (vm.count("help")) {
        cout << desc << endl;

        return 1;
    }

    if (!vm.count("sim-file") || !vm.count("out-dir")) {
        cout << "Missing options" << endl;
        cout << desc << endl;

        return 1;
    }

    generate_truth_from_sim(vm["sim-file"].as<string>(), vm["out-dir"].as<string>());

    return 0;
}

