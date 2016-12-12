//
// Created by fpeng on 2016/12/10.
//

#include <stdlib.h>
#include <string.h>
#include <glib.h>

#include "../../src/fileio.h"
#include "../../src/global_consts.h"
#include "../../src/objects/QCADDOContainer.h"


static gchar *input_file_name;
static gchar *output_dir_name;
static GOptionEntry entries[] = {
        {"input-file", 'i', 0, G_OPTION_ARG_STRING, &input_file_name, "input file name", NULL},
        {"output-dir", 'o', 0, G_OPTION_ARG_STRING, &output_dir_name, "output directory name", NULL},
        {NULL}
};

void generate_qca_and_sim_from_structure_file_imp(char *input_file_name, char *output_dir_name) {

    g_assert( g_file_test(input_file_name, G_FILE_TEST_EXISTS) );
    g_assert( g_file_test(output_dir_name, G_FILE_TEST_EXISTS) );

    //[1]load file into memory
    FILE *file = fopen(input_file_name, "rb");
    if (NULL == file) {
        fputs("Failed to open the structure file!", stderr);
        exit(1);
    }

    fseek (file, 0 , SEEK_END);
    long lsize = ftell (file);
    rewind (file);

    char *content = (char*)malloc(sizeof(char)*lsize);
    if (NULL == content) {
        fputs ("Failed to allocate memory!", stderr);
        exit (2);
    }

    size_t result = fread (content, 1, (size_t)lsize, file);
    if (result != lsize) {
        free(content);
        fclose(file);

        fputs ("Failed to read the file content", stderr);
        exit (3);
    }

    //[2]create design and get "Main Cell Layer"
    QCADSubstrate *sub = NULL;
    DESIGN *design = NULL;
    design = design_new(&sub);

    QCADLayer *layer = QCAD_LAYER(g_list_first(design->lstLayers)->data);
    QCADCell *cell = NULL;

    //[3]iterate the line of the content, and add cells in each line
    char cell_label[128];
    char index[8];
    int r = 0;
    gchar **lines = g_strsplit(content, "\n", -1);
    for (gchar **line = lines; *line; ++line, ++r) {

        char *line_cell = strtok(*line, "\t ");
        int c = 0;
        while (line_cell != NULL) {
            int line_cell_val = atoi(line_cell);
            switch (line_cell_val) {
                case -1:
                    //create cell
                    cell = QCAD_CELL(qcad_cell_new(100 + 20 * c, 100 + 20 * r));
                    //set cell function
                    qcad_cell_set_function(cell, QCAD_CELL_INPUT);
                    //set cell label
                    strcpy(cell_label, "I");
                    sprintf(index, "%d", r * 10 + c);
                    strcat(cell_label, index);
                    qcad_cell_set_label(cell, cell_label);
                    //add cell
                    qcad_do_container_add(QCAD_DO_CONTAINER(layer), QCAD_DESIGN_OBJECT(cell));
                    break;
                case -2:
                    //create cell
                    cell = QCAD_CELL(qcad_cell_new(100 + 20 * c, 100 + 20 * r));
                    //set cell function
                    qcad_cell_set_function(cell, QCAD_CELL_OUTPUT);
                    //set cell label
                    strcpy(cell_label, "O");
                    sprintf(index, "%d", r * 10 + c);
                    strcat(cell_label, index);
                    qcad_cell_set_label(cell, cell_label);
                    //add cell
                    qcad_do_container_add(QCAD_DO_CONTAINER(layer), QCAD_DESIGN_OBJECT(cell));
                    break;
                case 1:
                    //create cell
                    cell = QCAD_CELL(qcad_cell_new(100 + 20 * c, 100 + 20 * r));
                    //add cell
                    qcad_do_container_add(QCAD_DO_CONTAINER(layer), QCAD_DESIGN_OBJECT(cell));
                default:
                    break;
            }

            line_cell = strtok(NULL, "\t ");
            ++c;
        }
    }
    g_strfreev(lines);
    free(content);
    fclose(file);

    //[4]define vector table variable
    VectorTable *pvt = NULL;
    VectorTable_add_inputs(pvt, design);

    //[5]run simulation, and construct the corresponding simulation output data structure
    simulation_data *sim_data = run_simulation(BISTABLE, EXHAUSTIVE_VERIFICATION, design, pvt);
    SIMULATION_OUTPUT sim_output = {sim_data, design->bus_layout, FALSE};

    //[6]compute design file name and sim file name from input_file_name and output_dir_name
    gchar *base_name_with_appendix = g_path_get_basename(input_file_name);
    char *base_name = strtok(base_name_with_appendix, ".");

    char design_file_name[128];
    strcpy(design_file_name, output_dir_name);
    strcat(design_file_name, G_DIR_SEPARATOR_S);
    strcat(design_file_name, base_name);

    char sim_file_name[128];
    strcpy(sim_file_name, design_file_name);

    strcat(design_file_name, ".qca");
    strcat(sim_file_name, ".sim");

    //[7]generate design file and sim file
    create_file(design_file_name, design);
    create_simulation_output_file(sim_file_name, &sim_output);

    //[8]destroy design object, reclaim memory
    g_free(base_name_with_appendix);
    simulation_data_destroy(sim_data);
    design_destroy(design);
}

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

    g_assert( g_file_test(input_file_name, G_FILE_TEST_EXISTS) );
    g_assert( g_file_test(output_dir_name, G_FILE_TEST_EXISTS) );

    generate_qca_and_sim_from_structure_file_imp(input_file_name, output_dir_name);

    return 0;
}