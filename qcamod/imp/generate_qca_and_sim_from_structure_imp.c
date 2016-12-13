//
// Created by fpeng on 2016/12/2.
//

#include <stdio.h>
#include <string.h>

#include "../../src/fileio.h"
#include "../../src/global_consts.h"
#include "../../src/objects/QCADDOContainer.h"

#include <Python.h>


void generate_qca_and_sim_from_structure_imp(PyObject *structure, char *qca_file_name, char *sim_file_name) {
    //[1] assertions
    g_assert( PyList_Check(structure) );

    //[2]create design and get "Main Cell Layer"
    QCADSubstrate *sub = NULL;
    DESIGN *design = NULL;
    design = design_new(&sub);

    QCADLayer *layer = QCAD_LAYER(g_list_first(design->lstLayers)->data);
    QCADCell *cell = NULL;

    //[3]travelse structure and add cells
    char cell_label[128];
    char index[8];

    long long rsize = PyList_Size(structure);
    for (long long r=0; r<rsize; ++r) {
        PyObject *line = PyList_GET_ITEM(structure, r);
        g_assert( PyList_Check(line) );

        long long csize = PyList_Size(line);

        for (long long c=0; c<csize; ++c) {
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
                    strcpy(cell_label, "I");
                    sprintf(index, "%lld", r * 10 + c);
                    strcat(cell_label, index);
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
                    strcpy(cell_label, "O");
                    sprintf(index, "%lld", r * 10 + c);
                    strcat(cell_label, index);
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
    simulation_data *sim_data = run_simulation(BISTABLE, EXHAUSTIVE_VERIFICATION, design, pvt);
    SIMULATION_OUTPUT sim_output = {sim_data, design->bus_layout, FALSE};

    //[6]generate design file and sim file
    create_file(qca_file_name, design);
    create_simulation_output_file(sim_file_name, &sim_output);

    //[7]destroy design object, reclaim its memory
    simulation_data_destroy(sim_data);
    design_destroy(design);
}

