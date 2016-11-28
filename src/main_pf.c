//
// Created by fpeng on 2016/11/18.
//

#include <stdio.h>
#include <glib.h>
#include "fileio.h"
#include "global_consts.h"
#include "objects/QCADDOContainer.h"

static gchar *input_file_name;
static gchar *output_dir_name;
static GOptionEntry entries[] = {
        {"input-file", 'i', 0, G_OPTION_ARG_STRING, &input_file_name, "input file name", NULL},
        {"output-dir", 'o', 0, G_OPTION_ARG_STRING, &output_dir_name, "output directory name", NULL},
        {NULL}
};


int main(int argc, char **argv) {

    //[1]parse cmd line options
    GError *error = NULL;
    GOptionContext *context = NULL;
    context = g_option_context_new("-input output");
    g_option_context_add_main_entries (context, entries, NULL);
    if (!g_option_context_parse (context, &argc, &argv, &error)) {
        g_print ("option parsing failed: %s/n", error->message);
        exit (1);
    }

    //[2]create design and get "Main Cell Layer"
    QCADSubstrate *sub = NULL;
    DESIGN *design = NULL;
    design = design_new(&sub);

    QCADLayer *layer = QCAD_LAYER(g_list_first(design->lstLayers)->data);
    QCADCell *cell = NULL;

    //[3]read file and add cells
    gchar *contents;
    gsize len;
    if (g_file_get_contents(input_file_name, &contents, &len, error)) {

        gchar cell_label[128];
        char index[8];

        gchar **lines = g_strsplit(contents, "\n", -1);
        int i = 0;
        for (gchar **line = lines; *line; ++line, ++i) {

            gchar **line_cells = g_strsplit_set(*line, "\t\n ", -1);
            int j = 0;
            for (gchar **line_cell = line_cells; *line_cell; ++line_cell, ++j) {
                gint line_cell_val = atoi(*line_cell);
//                g_print("%d\n", line_cell_val);

                switch(line_cell_val) {
                    case -1:
                        //create cell
                        cell = QCAD_CELL(qcad_cell_new(100+20*i, 100+20*j));
                        //set cell function
                        qcad_cell_set_function(cell, QCAD_CELL_INPUT);
                        //set cell label
                        g_strlcpy(cell_label, "I", 128);
                        itoa(i, index, 10);
                        g_strlcat(cell_label, index, 128);
                        itoa(j, index, 10);
                        g_strlcat(cell_label, index, 128);
                        g_print("%s\n", cell_label);
                        qcad_cell_set_label(cell, cell_label);
                        //add cell
                        qcad_do_container_add(QCAD_DO_CONTAINER(layer), QCAD_DESIGN_OBJECT(cell));
                        break;
                    case -2:
                        //create cell
                        cell = QCAD_CELL(qcad_cell_new(100+20*i, 100+20*j));
                        //set cell function
                        qcad_cell_set_function(cell, QCAD_CELL_OUTPUT);
                        //set cell label
                        g_strlcpy(cell_label, "O", 128);
                        itoa(i, index, 10);
                        g_strlcat(cell_label, index, 128);
                        itoa(j, index, 10);
                        g_strlcat(cell_label, index, 128);
                        g_print("%s\n", cell_label);
                        qcad_cell_set_label(cell, cell_label);
                        //add cell
                        qcad_do_container_add(QCAD_DO_CONTAINER(layer), QCAD_DESIGN_OBJECT(cell));
                        break;
                    case 1:
                        //create cell
                        cell = QCAD_CELL(qcad_cell_new(100+20*i, 100+20*j));
                        //add cell
                        qcad_do_container_add(QCAD_DO_CONTAINER(layer), QCAD_DESIGN_OBJECT(cell));
                    case 0:
                        break;
                }

            }
            g_strfreev(line_cells);

//            g_print("\n");
        }
        g_strfreev(lines);

    } else {
        g_print("read file error : %s/n", error->message);
    }
    g_free(contents);

//    g_print("=========================================");

    //[4]define vector table variable
    VectorTable *pvt = NULL;
    VectorTable_add_inputs(pvt, design);

    //[5]run simulation, and construct the corresponding simulation output data structure
    simulation_data *sim_data = run_simulation(BISTABLE, EXHAUSTIVE_VERIFICATION, design, pvt);
    SIMULATION_OUTPUT sim_output = {sim_data, design->bus_layout, FALSE};

    //[6] generate design file
    gchar **path_names = g_strsplit_set(input_file_name, "\\/.", -1);
    gchar **base_name_p = NULL;
    for (base_name_p=path_names; *base_name_p; ++base_name_p) {
        if ((*(++base_name_p)) == NULL) {
            --base_name_p;
            --base_name_p;
            break;
        }
    }
    gchar *base_name = *base_name_p;

//    g_print("%s\n", base_name);

    gchar design_file_name[1024];
    g_strlcpy(design_file_name, output_dir_name, 1024);
#ifdef Win32
    g_strlcat(design_file_name, "\\", 1024);
#else
    g_strlcat(design_file_name, "/", 1024);
#endif
    g_strlcat(design_file_name, base_name, 1024);
    g_strlcat(design_file_name, ".qca", 1024);

//    g_print("%s\n", design_file_name);

    create_file(design_file_name, design);

    //[7]generate simulation output file
    gchar **design_name_splited = g_strsplit(design_file_name, ".", -1);
    gchar sim_file_name[1024];
    g_strlcpy(sim_file_name, *design_name_splited, 1024);
    g_strlcat(design_file_name, ".sim", 1024);
    create_simulation_output_file(sim_file_name, &sim_output);

    //[6]destroy design object, reclaim its memory
    design_destroy(design);

    return 0;
}