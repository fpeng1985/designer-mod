//
// Created by fpeng on 2016/11/18.
//

#include <stdio.h>
#include <string.h>
#include <glib.h>
#include "fileio.h"
#include "design.h"
#include "graph_dialog.h"
#include "global_consts.h"
#include "simulation.h"
#include "simulation_data.h"
#include "coherence_vector.h"
#include "graph_dialog_widget_data.h"
#include "bistable_simulation.h"

#include "objects/QCADDOContainer.h"
#include "objects/QCADLayer.h"
#include "objects/QCADCell.h"
#include "exp_array.h"


int main(int argc, char **argv) {

    QCADSubstrate *sub = NULL;
    DESIGN *design = NULL;
    design = design_new(&sub);

    VectorTable *pvt = NULL;

    QCADLayer *layer = QCAD_LAYER(g_list_first(design->lstLayers->data));

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

    VectorTable_add_inputs(pvt, design);

    gchar *design_file  = "c:\\Users\\fpeng\\Desktop\\qcad\\layer.qca";
    create_file(design_file, design);

    simulation_data *sim_data = run_simulation(BISTABLE, EXHAUSTIVE_VERIFICATION, design, pvt);

    SIMULATION_OUTPUT sim_output = {sim_data, design->bus_layout, FALSE};

    gchar *output_file = "c:\\Users\\fpeng\\Desktop\\qcad\\sim_output";
    create_simulation_output_file(output_file, &sim_output);

    design_destroy(design);
    VectorTable_free(pvt);

    return 0;
}