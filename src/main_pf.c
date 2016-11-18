//
// Created by fpeng on 2016/11/18.
//

#include <stdio.h>
#include <glib.h>
#include "fileio.h"
#include "global_consts.h"
#include "objects/QCADDOContainer.h"


int main(int argc, char **argv) {

    //[1]create design
    QCADSubstrate *sub = NULL;
    DESIGN *design = NULL;
    design = design_new(&sub);

    //[2]insert cells into "Main Cell Layer" of the design
    QCADLayer *layer = QCAD_LAYER(g_list_first(design->lstLayers)->data);
    QCADCell *cell = NULL;

    cell = QCAD_CELL(qcad_cell_new(200, 200));
    qcad_cell_set_function(cell, QCAD_CELL_INPUT);
    qcad_cell_set_label(cell, "A");
    qcad_do_container_add(QCAD_DO_CONTAINER(layer), QCAD_DESIGN_OBJECT(cell));

    cell = QCAD_CELL(qcad_cell_new(220, 200));
    qcad_do_container_add(QCAD_DO_CONTAINER(layer), QCAD_DESIGN_OBJECT(cell));

    cell = QCAD_CELL(qcad_cell_new(240,200));
    qcad_cell_set_function(cell, QCAD_CELL_OUTPUT);
    qcad_cell_set_label(cell, "F");
    qcad_do_container_add(QCAD_DO_CONTAINER(layer), QCAD_DESIGN_OBJECT(cell));

    cell = QCAD_CELL(qcad_cell_new(220, 220));
    qcad_cell_set_function(cell, QCAD_CELL_INPUT);
    qcad_cell_set_label(cell, "B");
    qcad_do_container_add(QCAD_DO_CONTAINER(layer), QCAD_DESIGN_OBJECT(cell));

    cell = QCAD_CELL(qcad_cell_new(220, 180));
    qcad_cell_set_function(cell, QCAD_CELL_INPUT);
    qcad_cell_set_label(cell, "C");
    qcad_do_container_add(QCAD_DO_CONTAINER(layer), QCAD_DESIGN_OBJECT(cell));

    //[3]define vector table variable
    VectorTable *pvt = NULL;
    VectorTable_add_inputs(pvt, design);

    //[4]run simulation, and construct the corresponding simulation output data structure
    simulation_data *sim_data = run_simulation(BISTABLE, EXHAUSTIVE_VERIFICATION, design, pvt);
    SIMULATION_OUTPUT sim_output = {sim_data, design->bus_layout, FALSE};

    //[5] generate qca ${HOME}/design.qca and simulation output file ${HOME}/sim_output.txt
    GString *home = NULL;

    home = g_string_new(getenv("HOME"));
    gchar *design_file  = (g_string_append(home, "\\design.qca"))->str;
    create_file(design_file, design);

    home = g_string_new(getenv("HOME"));
    gchar *output_file = (g_string_append(home, "\\sim_output.txt"))->str;
    create_simulation_output_file(output_file, &sim_output);

    //[6]destroy design object, reclaim its memory
    design_destroy(design);

    return 0;
}