//
// Created by fpeng on 2016/12/2.
//

#include <string>
#include <vector>
#include <set>
#include <algorithm>
#include <iterator>

#include <iostream>
#include <fstream>
#include <sstream>

#include <cassert>
using namespace std;

#include "grammar.hpp"

std::vector<std::vector<int>> generate_truth_from_sim_imp(const std::string &sim_file_name, unsigned long input_size) {
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

    sort(traces.begin(), traces.end(), [](const Trace &a, const Trace &b){
        return a.data_labels < b.data_labels;
    });

    //feed parsed data truth value set removing redundant values
    size_t sample_size = traces[0].trace_data.size();

    for (size_t i=0; i<traces.size(); ++i) {
        assert(traces[i].trace_data.size() == sample_size);
    }

    set<vector<int>> truth;
    for (size_t i=0; i<sample_size; ++i) {
        bool is_valid = true;
        for (size_t j=input_size; j<traces.size(); ++j) {
            if ( -0.5 < traces[j].trace_data[i] && traces[j].trace_data[i] < 0.5) {
                is_valid = false;
                break;
            }
        }

        if (is_valid) {
            vector<int> truth_val;
            for (size_t j=0; j<input_size; ++j) {
                truth_val.push_back( traces[j].trace_data[i]>0 ? 1 : 0 );
            }

            for (size_t j=input_size; j<traces.size(); ++j) {
                truth_val.push_back( traces[j].trace_data[i]>0 ? 1 : 0 );
            }

            assert( truth_val.size() == traces.size());

            truth.insert(truth_val);
        }
    }

    //since std::set has sorting function, the truth_table has been sorted already
    vector<vector<int>> truth_table(truth.begin(), truth.end());

    return truth_table;
}
