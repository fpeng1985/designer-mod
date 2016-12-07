//
// Created by fpeng on 2016/12/2.
//

#include <string>

#include <vector>
#include <set>
#include <iterator>
#include <algorithm>

#include <iostream>
#include <fstream>
#include <sstream>

#include <cassert>
using namespace std;

#include <boost/filesystem.hpp>
namespace fs = boost::filesystem;

#include "grammar.hpp"


void generate_truth_from_sim(const std::string &sim_file_name, const std::string &output_dir) {
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

    size_t output_index = 0;
    bool not_encountered_out_label = true;
    vector<string> labels;
    for (size_t i=0; i<traces.size(); ++i) {
        assert(traces[i].trace_data.size() == sample_size);

        labels.push_back(traces[i].data_labels);

        if (traces[i].data_labels.find("O") != string::npos && not_encountered_out_label) {
            output_index = i;

            not_encountered_out_label = false;
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

    //cout << "generating truth value file in " << truth_file_path.generic_string() << endl;

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
