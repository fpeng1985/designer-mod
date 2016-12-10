%module generate_qca_and_sim_from_structure
%{
/* Put headers and other declarations here */
extern void generate_qca_and_sim_from_structure(char *structure_file_name, char *output_dir_name);
%}

extern void generate_qca_and_sim_from_structure(char *structure_file_name, char *output_dir_name);