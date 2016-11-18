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


int main(int argc, char **argv) {
    gchar *file = "c:\\msys64\\home\\fpeng\\layer.qca";

    QCADSubstrate *sub = NULL;
    DESIGN *design = NULL;
    design = design_new(&sub);

    QCADLayer *layer = QCAD_LAYER(g_list_first(design->lstLayers->data));

    QCADCell *cell = NULL;

    cell = QCAD_CELL(qcad_cell_new(200, 200));
    qcad_cell_set_function(cell, QCAD_CELL_INPUT);
    qcad_do_container_add(QCAD_DO_CONTAINER(layer), QCAD_DESIGN_OBJECT(cell));

    cell = QCAD_CELL(qcad_cell_new(220, 200));
    qcad_do_container_add(QCAD_DO_CONTAINER(layer), QCAD_DESIGN_OBJECT(cell));

    cell = QCAD_CELL(qcad_cell_new(240,200));
    qcad_cell_set_function(cell, QCAD_CELL_OUTPUT);
    qcad_do_container_add(QCAD_DO_CONTAINER(layer), QCAD_DESIGN_OBJECT(cell));

    cell = QCAD_CELL(qcad_cell_new(220, 220));
    qcad_do_container_add(QCAD_DO_CONTAINER(layer), QCAD_DESIGN_OBJECT(cell));

    cell = QCAD_CELL(qcad_cell_new(220, 180));
    qcad_do_container_add(QCAD_DO_CONTAINER(layer), QCAD_DESIGN_OBJECT(cell));


    create_file(file, design);

    design_destroy(design);

//    QCADLayer *layer = qcad_layer_new(LAYER_TYPE_CELLS, LAYER_STATUS_ACTIVE, "Main Cell Layer");
//    qcad_design_object_serialize (QCAD_DESIGN_OBJECT(layer), fp);

    return 0;
}