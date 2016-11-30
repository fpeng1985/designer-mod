#include <string>

#include <vector>
#include <map>
#include <iterator>
#include <algorithm>

#include <iostream>
#include <fstream>
#include <sstream>

#include <cassert>

#include "sim_parser.hpp"

#include <boost/filesystem.hpp>
#include <boost/program_options.hpp>

using namespace std;
namespace fs = boost::filesystem;

void generate_truth_file_from_sim(const std::string &sim_file_name, const std::string &output_dir) {
    //read file into string
    ifstream ifs(sim_file_name, std::ios::in);
    istream_iterator<string> ifs_it(ifs), ifs_end();

    vector<string> contents;

    bool flag = false;
    string line;
    while (getline(ifs, line)) {
        if (line == "[TRACES]") {
            flag = true;
        } else if (line == "[#TRACES]") {
            flag = false;
        }

        if (flag || line == "[#TRACES]") {
            contents.push_back(line);
        }

    }

    ifs.close();

    string content = "";
    for (auto &str : contents) {
        content += " " + str;
    }

    //parse content into container
    vector<Trace> traces;
    parse_sim_file_by_spirit(content.begin(), content.end(), traces);

    assert(!traces.empty());

    //feed parsed data truth value set removing redandunt values
    size_t sample_size = traces[0].trace_data.size();

    size_t output_index = -1;
    vector<string> labels;
    for (size_t i=0; i<traces.size(); ++i) {
        assert(traces[i].trace_data.size() == sample_size);

        labels.push_back(traces[i].data_labels);

        if (traces[i].data_labels.find("O") != string::npos && output_index==-1) {
            output_index = i;
        }
    }

    set<vector<int>> truth;
    for (size_t i=0; i<sample_size; ++i) {
        bool is_valid = true;
        for (size_t j=output_index; j<traces.size(); ++j) {
            if ( -0.5 < traces[j].trace_data[i] && traces[j].trace_data[i] < 0.5) {
                is_valid = false;
                break;
            }
        }

        if (is_valid) {
            vector<int> truth_val;
            for (size_t j=0; j<output_index; ++j) {
                truth_val.push_back( traces[j].trace_data[i]>0 ? 1 : 0 );
            }

            for (size_t j=output_index; j<traces.size(); ++j) {
                truth_val.push_back( traces[j].trace_data[i]>0 ? 1 : 0 );
            }

            assert( truth_val.size() == traces.size());

            truth.insert(truth_val);
        }
    }

    //generate output
    fs::path sim_file_path(sim_file_name);
    fs::path truth_file_path(output_dir);
    truth_file_path /= (sim_file_path.stem().string() + ".truth");

    cout << "generating truth value file in " << truth_file_path.string() << endl;

    ofstream ofs(truth_file_path.string(), ios::out);

    for (size_t i=0; i<labels.size(); ++i) {
        if (i == labels.size()-1) {
            ofs << labels[i] << endl;
        } else {
            ofs <<  labels[i] << '\t';
        }
    }

    for (auto &truth_val : truth) {
        assert(truth_val.size() == labels.size());

        for (size_t i=0; i<truth_val.size(); ++i) {
            if (i == truth_val.size()-1) {
                ofs << truth_val[i] << endl;
            } else {
                ofs <<  truth_val[i] << '\t';
            }
        }
    }
    ofs << endl;

    ofs.close();
}



int main(int argc, char *argv[]) {
//    generate_truth_file_from_sim("C:\\Users\\fpeng\\Documents\\sim_manager\\majority_gate_1\\1\\1.sim",
//                                 "C:\\Users\\fpeng\\Documents\\sim_manager\\majority_gate_1\\1");
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

    generate_truth_file_from_sim(vm["sim-file"].as<string>(), vm["out-dir"].as<string>());

    return 0;
}

