//
// Created by fpeng on 2016/12/2.
//

#include <stdio.h>
#include <glib.h>

#include "../../src/fileio.h"
#include "../../src/global_consts.h"
#include "../../src/objects/QCADDOContainer.h"

#include <Python.h>

void generate_qca_and_sim_from_structure_imp(PyObject *structure, char *qca_file_name, char *sim_file_name) {
    //[1] assertions
    g_assert( PyList_Check(structure) );

    //[2]create design and get "Main Cell Layer"
    GError *error = NULL;
    QCADSubstrate *sub = NULL;
    DESIGN *design = NULL;
    design = design_new(&sub);

    QCADLayer *layer = QCAD_LAYER(g_list_first(design->lstLayers)->data);
    QCADCell *cell = NULL;

    //[3]travelse structure and add cells
    gchar cell_label[128];
    char index[8];

    Py_ssize_t rsize = PyList_Size(structure);

    for (Py_ssize_t r=0; r<rsize; ++r) {
        PyObject *line = PyList_GET_ITEM(structure, r);
        g_assert( PyList_Check(line) );

        Py_ssize_t csize = PyList_Size(line);

        for (Py_ssize_t c=0; c<csize; ++c) {
            PyObject *op = PyList_GET_ITEM(line, c);
            g_assert( PyLong_Check(op));

            long cell_type = PyLong_AsLong(op);
            switch(cell_type) {
                case -1:
                    //create cell
                    cell = QCAD_CELL(qcad_cell_new(100+20*c, 100+20*r));
                    //set cell function
                    qcad_cell_set_function(cell, QCAD_CELL_INPUT);
                    //set cell label
                    g_strlcpy(cell_label, "I", 128);
                    sprintf(index, "%lld", r);
                    g_strlcat(cell_label, index, 128);
                    sprintf(index, "%lld", c);
                    g_strlcat(cell_label, index, 128);
                    qcad_cell_set_label(cell, cell_label);
                    //add cell
                    qcad_do_container_add(QCAD_DO_CONTAINER(layer), QCAD_DESIGN_OBJECT(cell));
                    break;
                case -2:
                    //create cell
                    cell = QCAD_CELL(qcad_cell_new(100+20*c, 100+20*r));
                    //set cell function
                    qcad_cell_set_function(cell, QCAD_CELL_OUTPUT);
                    //set cell label
                    g_strlcpy(cell_label, "O", 128);
                    sprintf(index, "%lld", r);
                    g_strlcat(cell_label, index, 128);
                    sprintf(index, "%lld", c);
                    g_strlcat(cell_label, index, 128);
                    qcad_cell_set_label(cell, cell_label);
                    //add cell
                    qcad_do_container_add(QCAD_DO_CONTAINER(layer), QCAD_DESIGN_OBJECT(cell));
                    break;
                case 1:
                    //create cell
                    cell = QCAD_CELL(qcad_cell_new(100+20*c, 100+20*r));
                    //add cell
                    qcad_do_container_add(QCAD_DO_CONTAINER(layer), QCAD_DESIGN_OBJECT(cell));
                default:
                    break;
            }
        }
    }

    //[4]define vector table variable
    VectorTable *pvt = NULL;
    VectorTable_add_inputs(pvt, design);

    //[5]run simulation, and construct the corresponding simulation output data structure
    //g_print("generating qca and sim file from %s\n", input_file_name);
    simulation_data *sim_data = run_simulation(BISTABLE, EXHAUSTIVE_VERIFICATION, design, pvt);
    SIMULATION_OUTPUT sim_output = {sim_data, design->bus_layout, FALSE};

    //[7]generate design file and sim file
    create_file(qca_file_name, design);

    create_simulation_output_file(sim_file_name, &sim_output);

    //[8]destroy design object, reclaim its memory
    design_destroy(design);
}