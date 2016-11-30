#include <string>

#include <vector>
#include <map>
#include <iterator>
#include <algorithm>

#include <iostream>
#include <fstream>
#include <sstream>

#include "sim_parser.hpp"

int generate_truth_file_from_sim(const std::string &sim_file_name) {
    using namespace std;

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

    string content = "";
    for (auto &str : contents) {
        content += " " + str;
    }

    vector<Trace> traces;

    parse_sim_file_by_spirit(content.begin(), content.end(), traces);

    cout << traces.size() << endl;
    for ( auto &trace : traces) {
        cout << trace.data_labels << endl;
    }
}



int main(int argc, char *argv[]) {
//    parse_sim_file("C:\\Users\\fpeng\\Documents\\sim_manager\\majority_gate_1\\1\\2.sim");
    generate_truth_file_from_sim("C:\\Users\\fpeng\\Documents\\sim_manager\\majority_gate_1\\1\\2.sim");


    return 0;
}

