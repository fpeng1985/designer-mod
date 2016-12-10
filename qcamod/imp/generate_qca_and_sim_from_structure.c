//
// Created by fpeng on 2016/12/2.
//
#include "generate_qca_and_sim_from_structure.h"

#include <stdio.h>
#include <glib.h>

#include "../../src/fileio.h"
#include "../../src/global_consts.h"
#include "../../src/objects/QCADDOContainer.h"
int main()
{
    FILE * pFile;
    long lSize;
    char * buffer;
    size_t result;

    /* 若要一个byte不漏地读入整个文件，只能采用二进制方式打开 */
    pFile = fopen ("test.txt", "rb" );
    if (pFile==NULL)
    {
        fputs ("File error",stderr);
        exit (1);
    }

    /* 获取文件大小 */
    fseek (pFile , 0 , SEEK_END);
    lSize = ftell (pFile);
    rewind (pFile);

    /* 分配内存存储整个文件 */
    buffer = (char*) malloc (sizeof(char)*lSize);
    if (buffer == NULL)
    {
        fputs ("Memory error",stderr);
        exit (2);
    }

    /* 将文件拷贝到buffer中 */
    result = fread (buffer,1,lSize,pFile);
    if (result != lSize)
    {
        fputs ("Reading error",stderr);
        exit (3);
    }
    /* 现在整个文件已经在buffer中，可由标准输出打印内容 */
    printf("%s", buffer);

    /* 结束演示，关闭文件并释放内存 */
    fclose (pFile);
    free (buffer);







    char str[80] = "This.is - www.w3cschool.cc - web.site";

    char d1[2] = "-";
    char d2[2] = ".";

    char *line;
    char *tok;

    /* 获取第一个子字符串 */
    line = strtok(str, d1);

    /* 继续获取其他的子字符串 */
    while( line != NULL ) {

        size_t sz = strlen(line) + 1;
        char *tmp = (char *)malloc(sz);
        memcpy(tmp, line, sz);

        char *t = strtok(tmp, d2);
        while (t!= NULL) {
            printf("%s\n", t);

            t = strtok(NULL, d2);
        }

        free(tmp);

        line = strtok(NULL, d1);
    }

    return(0);
}
void generate_qca_and_sim_from_structure(char *input_file_name, char *output_dir_name) {

    g_assert( g_file_test(input_file_name, G_FILE_TEST_EXISTS) );
    g_assert( g_file_test(output_dir_name, G_FILE_TEST_EXISTS) );

    GError *error = NULL;
    //[2]create design and get "Main Cell Layer"
    QCADSubstrate *sub = NULL;
    DESIGN *design = NULL;
    design = design_new(&sub);

    QCADLayer *layer = QCAD_LAYER(g_list_first(design->lstLayers)->data);
    QCADCell *cell = NULL;

    //[3]read file and add cells
    gchar *contents;
    gsize len;
    if (g_file_get_contents(input_file_name, &contents, &len, &error)) {

        gchar cell_label[128];
        char index[8];

        gchar **lines = g_strsplit(contents, "\n", -1);
        int r = 0;
        for (gchar **line = lines; *line; ++line, ++r) {

            gchar **line_cells = g_strsplit_set(*line, "\t\n ", -1);
            int c = 0;
            for (gchar **line_cell = line_cells; *line_cell; ++line_cell, ++c) {
                gint line_cell_val = atoi(*line_cell);

                switch(line_cell_val) {
                    case -1:
                        //create cell
                        cell = QCAD_CELL(qcad_cell_new(100+20*c, 100+20*r));
                        //set cell function
                        qcad_cell_set_function(cell, QCAD_CELL_INPUT);
                        //set cell label
                        g_strlcpy(cell_label, "I", 128);
                        sprintf(index, "%d", r);
//                        itoa(r, index, 10);
                        g_strlcat(cell_label, index, 128);
                        sprintf(index, "%d", c);
//                        itoa(c, index, 10);
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
                        sprintf(index, "%d", r);
//                        itoa(r, index, 10);
                        g_strlcat(cell_label, index, 128);
                        sprintf(index, "%d", c);
//                        itoa(c, index, 10);
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
            g_strfreev(line_cells);

        }
        g_strfreev(lines);

    } else {
        g_print("read file error : %s/n", error->message);
    }
    g_free(contents);

    //[4]define vector table variable
    VectorTable *pvt = NULL;
    VectorTable_add_inputs(pvt, design);

    //[5]run simulation, and construct the corresponding simulation output data structure
    //g_print("generating qca and sim file from %s\n", input_file_name);

    simulation_data *sim_data = run_simulation(BISTABLE, EXHAUSTIVE_VERIFICATION, design, pvt);
    SIMULATION_OUTPUT sim_output = {sim_data, design->bus_layout, FALSE};

    //[6] compute design file name and sim file name from input_file_name and output_dir_name
    gchar *base_name_with_appendix = g_path_get_basename(input_file_name);
    GString *base_name_str = g_string_new(base_name_with_appendix);
    base_name_str = g_string_truncate(base_name_str, g_strstr_len(base_name_with_appendix, -1, ".") - base_name_with_appendix);
    g_free(base_name_with_appendix);
    gchar *base_name = g_string_free(base_name_str, FALSE);

    GString *design_file_name_str = g_string_new(output_dir_name);
    g_string_append(design_file_name_str, G_DIR_SEPARATOR_S);
    g_string_append(design_file_name_str, base_name);
    g_free(base_name);

    GString *sim_file_name_str = g_string_new(design_file_name_str->str);

    g_string_append(design_file_name_str, ".qca");
    g_string_append(sim_file_name_str, ".sim");

//    g_print("%s\n", design_file_name_str->str);
//    g_print("%s\n", sim_file_name_str->str);

    //[7]generate design file and sim file
    create_file(design_file_name_str->str, design);
    g_string_free(design_file_name_str, TRUE);

    create_simulation_output_file(sim_file_name_str->str, &sim_output);
    g_string_free(sim_file_name_str, TRUE);


    //[8]destroy design object, reclaim its memory
    design_destroy(design);
}