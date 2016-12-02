%module generate_truth_from_sim
%include "std_string.i"
%{
/* Put headers and other declarations here */
extern void generate_truth_from_sim(const std::string &sim_file_name, const std::string &output_dir);
%}

extern void generate_truth_from_sim(const std::string &sim_file_name, const std::string &output_dir);
