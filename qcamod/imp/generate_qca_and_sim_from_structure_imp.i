%module generate_qca_and_sim_from_structure_imp
%{
/* Put headers and other declarations here */
extern void generate_qca_and_sim_from_structure_imp(PyObject *structure, char *output_dir_name, char *design_name);
%}

extern void generate_qca_and_sim_from_structure_imp(PyObject *structure, char *output_dir_name, char *design_name);
