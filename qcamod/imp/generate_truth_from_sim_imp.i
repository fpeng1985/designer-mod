%module generate_truth_from_sim_imp
%include "std_string.i"
%include "std_vector.i"
namespace std {
    %template(vi)  vector<int>;
    %template(vvi) vector< vector<int> >;
};

%{
/* Put headers and other declarations here */
extern std::vector<std::vector<int>> generate_truth_from_sim_imp(const std::string &sim_file_name, unsigned long input_size);
%}

extern std::vector<std::vector<int>> generate_truth_from_sim_imp(const std::string &sim_file_name, unsigned long input_size);
