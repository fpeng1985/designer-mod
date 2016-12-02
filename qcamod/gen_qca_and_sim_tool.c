//
// Created by fpeng on 2016/11/18.
//

#include <stdlib.h>
#include <glib.h>

#include "generate_qca_and_sim_from_structure.h"

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

    g_assert( g_file_test(input_file_name, G_FILE_TEST_EXISTS) );
    g_assert( g_file_test(output_dir_name, G_FILE_TEST_EXISTS) );

    generate_qca_and_sim_from_structure(input_file_name, output_dir_name);

    return 0;
}