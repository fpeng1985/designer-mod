#include <string>

#include <vector>
#include <map>
#include <iterator>
#include <algorithm>

#include <iostream>
#include <fstream>
#include <sstream>

//#include <boost/xpressive/xpressive.hpp>
//#include <boost/xpressive/regex_actions.hpp>

#include <boost/spirit/include/qi.hpp>
#include <boost/spirit/include/karma.hpp>
#include <boost/spirit/include/phoenix_operator.hpp>
namespace qi    = boost::spirit::qi;
namespace karma = boost::spirit::karma;
namespace asc = boost::spirit::ascii;

/*
template <class Type>
Type string_to_num(const std::string& str)
{
    std::istringstream iss(str);
    Type num;
    iss >> num;
    return num;
}

int parse_sim_file( const std::string &sim_file_name)
{
    using namespace std;
    using namespace boost::xpressive;

    //read file into string
    ifstream ifs(sim_file_name, std::ios::in);
    istream_iterator<string> ifs_it(ifs), ifs_end();

    vector<string> contents;

    bool flag = false;
    string line;
    while (getline(ifs, line)) {
        if (line == "[TRACES]") {
            flag = true;
        } else if (line == "[#TRACES]") {
            flag = false;
        }

        if (flag || line == "[#TRACES]") {
            contents.push_back(line);
        }

    }

    string content = "";
    for (auto &str : contents) {
        content += " " + str;
    }

    ofstream ofs("output.txt", ios::out);
    ofs << content << endl;

    //define container
    map<string, vector<double>> trace_container;

    //define parsing grammar

    sregex trace_data_item  = !_s >> !as_xpr('-') >> +_d >> '.' >> +_d >> icase('e') >> (as_xpr('+') | as_xpr('-')) >> +_d >> !_s;
    sregex trace_data = !_s >> "[TRACE_DATA]" >> +trace_data_item >> "[#TRACE_DATA]" >> !_s;
    sregex data_labels = !_s >> "data_labels=" >> +alnum >> !_s >> !(+_d) >> !_s;
    sregex trace_function = !_s >> "trace_function=" >> +_d >> !_s;
    sregex drawtrace = !_s >> "drawtrace=" >> +alpha >> !_s;
    sregex trace = !_s >> "[TRACE]" >> data_labels >> trace_function >> drawtrace >> trace_data >> "[#TRACE]" >> !_s;
    sregex traces = !_s >> "[TRACES]" >> +trace >> "[#TRACES]" >> !_s;

    smatch what;


    if (regex_match(string("-8.005773e-004 "), what, trace_data_item)) {
        cout << "trace_data_item match" << endl;
    }


    if (regex_match(string("[TRACE_DATA] -8.005773e-004 -8.005773e-004 -8.005773e-004 -8.005773e-004 -8.005773e-004 [#TRACE_DATA]"), what, trace_data)) {
        cout << "trace_data match" << endl;
    }

    if (regex_match(string("data_labels=CKL 3"), what, data_labels)) {
        cout << "data_labels match" << endl;
    }

    if( regex_match(string("trace_function=1"), what, trace_function) ) {
        cout << "trace function match" << endl;
    }

    if( regex_match(string("drawtrace=TRUE"), what, drawtrace) ) {
        cout << "drawtrace match" << endl;
    }

    if( regex_match(string("[TRACE] "
                                   "data_labels=CLOCK 0 "
                                   "trace_function=3 "
                                   "drawtrace=TRUE "
                                   "[TRACE_DATA] "
                                   "9.800000e-022 9.800000e-022 9.800000e-022 9.800000e-022 9.800000e-022 "
                                   "9.800000e-022 9.800000e-022 9.800000e-022 9.800000e-022 9.800000e-022 "
                                   "9.800000e-022 9.800000e-022 9.800000e-022 9.800000e-022 9.800000e-022 "
                                   "9.800000e-022 9.800000e-022 9.800000e-022 9.800000e-022 9.800000e-022 "
                                   "[#TRACE_DATA] "
                                   "[#TRACE]") ,
                    what, trace) ) {
        cout << "trace match" << endl;
    }
    if( regex_match(string(
            ""
                    " [TRACES] "
                    "[TRACE] "
                    "data_labels=CLOCK 0 "
                    "trace_function=3 "
                    "drawtrace=TRUE "
                    "[TRACE_DATA] "
                    "9.800000e-022 9.800000e-022 9.800000e-022 9.800000e-022 9.800000e+022 "
                    "9.800000e-022 9.800000e-022 9.800000e-022 9.800000e-022 9.800000e+022 "
                    "9.800000e-022 9.800000e-022 9.800000e-022 9.800000e-022 9.800000e-022 "
                    "9.800000e-022 9.800000e-022 9.800000e-022 9.800000e-022 9.800000e-022 "
                    "[#TRACE_DATA] "
                    "[#TRACE] "
                    "[TRACE] "
                    "data_labels=CLOCK 0 "
                    "trace_function=3 "
                    "drawtrace=TRUE "
                    "[TRACE_DATA] "
                    "9.800000e-022 9.800000e-022 9.800000e-022 9.800000e-022 9.800000e-022 "
                    "9.800000e-022 9.800000e-022 9.800000e-022 9.800000e-022 9.800000e-022 "
                    "9.800000e-022 9.800000e-022 9.800000e-022 9.800000e-022 9.800000e-022 "
                    "9.800000e-022 9.800000e-022 9.800000e-022 9.800000e-022 9.800000e-022 "
                    "[#TRACE_DATA] "
                    "[#TRACE] "
                    "[#TRACES] "
                    ) ,
                    what, traces) ) {
        cout << "traces match" << endl;
    }

//    if( regex_match(content, what, traces) ) {
//        cout << "match" << endl;
//    }


    return 0;
}
*/

struct Trace {
    std::string data_labels;
    int trace_function;
    bool drawtrace;
    std::vector<double> trace_data;
};

BOOST_FUSION_ADAPT_STRUCT(
        Trace,
        (std::string, data_labels)
        (int,      trace_function)
        (bool,      drawtrace)
        (std::vector<double>, trace_data)
)


struct DrawTraceSymbolTable : qi::symbols<char, bool> {
    DrawTraceSymbolTable() {
        add
                ("TRUE",  true)
                ("FALSE", false)
                ;
    }
} draw_trace_symbol;

template<typename Iterator>
struct SimParser : qi::grammar<Iterator, std::vector<Trace>(), asc::space_type> {

    SimParser() : SimParser::base_type(start) {

        using qi::int_;
        using qi::double_;
        using qi::lit;

//        using qi::eoi;
        using qi::eps;

        using qi::_val;
        using qi::_1;

        using qi::lexeme;


        trace_data_item %= double_;
        trace_data %= lit("[TRACE_DATA]") >> +trace_data_item >> lit("[#TRACE_DATA]");
        data_labels = eps[_val=""] >> lit("data_labels=") >> lexeme[+((~qi::space)[_val+=_1])] >> -(asc::digit[_val+=" ", _val+=_1]);
        trace_function %= lit("trace_function=") >> int_;
        drawtrace %= lit("drawtrace=") >> draw_trace_symbol;
        trace %= lit("[TRACE]") >> data_labels >> trace_function >> drawtrace >> +trace_data >> lit("[#TRACE]");
        start %= lit("[TRACES]") >> +trace >> lit("[#TRACES]");
    }

//    static DrawTraceSymbolTable  draw_trace_symbol;

    qi::rule<Iterator, double(), asc::space_type> trace_data_item;
    qi::rule<Iterator, std::vector<double>(), asc::space_type> trace_data;
    qi::rule<Iterator, std::string(), asc::space_type> data_labels;
    qi::rule<Iterator, int(), asc::space_type> trace_function;
    qi::rule<Iterator, bool(), asc::space_type> drawtrace;
    qi::rule<Iterator, Trace(), asc::space_type> trace;
    qi::rule<Iterator, std::vector<Trace>(), asc::space_type> start;

};//end template

//template<typename Iterator>
//DrawTraceSymbolTable SimParser<Iterator>::draw_trace_symbol;

template<typename Iterator>
int parse_sim_file_by_spirit(Iterator first, Iterator last, std::vector<Trace> &traces) {
    SimParser<Iterator> parser;
    qi::phrase_parse(first, last, parser, asc::space, traces);
}


int generate_truth_file_from_sim(const std::string &sim_file_name) {
    using namespace std;

    //read file into string
    ifstream ifs(sim_file_name, std::ios::in);
    istream_iterator<string> ifs_it(ifs), ifs_end();

    vector<string> contents;

    bool flag = false;
    string line;
    while (getline(ifs, line)) {
        if (line == "[TRACES]") {
            flag = true;
        } else if (line == "[#TRACES]") {
            flag = false;
        }

        if (flag || line == "[#TRACES]") {
            contents.push_back(line);
        }

    }

    string content = "";
    for (auto &str : contents) {
        content += " " + str;
    }

    vector<Trace> traces;

    parse_sim_file_by_spirit(content.begin(), content.end(), traces);

    cout << traces.size() << endl;
    for ( auto &trace : traces) {
        cout << trace.data_labels << endl;
    }
}



int main(int argc, char *argv[]) {
//    parse_sim_file("C:\\Users\\fpeng\\Documents\\sim_manager\\majority_gate_1\\1\\2.sim");
    parse_sim_file_by("C:\\Users\\fpeng\\Documents\\sim_manager\\majority_gate_1\\1\\2.sim");

    using namespace std;

    using qi::rule;
    using qi::_val;
    using qi::_1;
    using qi::lit;
    using qi::eps;

    std::string content;

    content = "-9.800000e-022";
    double val;
    if ( qi::phrase_parse(content.begin(), content.end(), qi::double_, asc::space, val) ) {
        std::cout << "data item match" << std::endl;
    }

    content = "[TRACE_DATA] -8.005773e-004 -8.005773e-004 -8.005773e-004 -8.005773e-004 -8.005773e-004 [#TRACE_DATA]";
    qi::rule<std::string::iterator, std::vector<double>(), asc::space_type> trace_data;
    trace_data %= qi::lit("[TRACE_DATA]") >> +qi::double_>> qi::lit("[#TRACE_DATA]") ;
    vector<double>  val1;
    if ( qi::phrase_parse(content.begin(), content.end(), trace_data, asc::space, val1) ) {
        std::cout << "data match" << std::endl;
    }

    using qi::lexeme;
    content = "data_labels=CKL 3";
    qi::rule<std::string::iterator, std::string(), asc::space_type> data_labels;
    data_labels = eps[_val=""] >> lit("data_labels=") >> lexeme[+((~qi::space)[_val+=_1])] >> -(asc::digit[_val+=" ", _val+=_1]);

//                                                      +(asc::alnum[cout << _1<<endl,_val+=_1]) >> *(asc::digit[_val += _1]);
    std::string val2;
    if ( qi::phrase_parse(content.begin(), content.end(), data_labels, asc::space, val2) ) {
        std::cout << "label match" << std::endl;
        std::cout << val2 << endl;
    }


    using qi::int_;
    content = "trace_function=1";
    qi::rule<std::string::iterator, int(), asc::space_type> trace_function;
    trace_function %= lit("trace_function=") >> int_;
    int val3;
    if ( qi::phrase_parse(content.begin(), content.end(), trace_function, asc::space, val3) ) {
        std::cout << "funtion match" << std::endl;
        std::cout << val3 << endl;
    }

    content = "drawtrace=FALSE";
    qi::rule<std::string::iterator, bool(), asc::space_type> drawtrace;
    drawtrace %= lit("drawtrace=") >> draw_trace_symbol;
    bool val4;
    if ( qi::phrase_parse(content.begin(), content.end(), drawtrace, asc::space, val4) ) {
        std::cout << "draw trace match" << std::endl;
        std::cout << val4 << endl;
    }

    content = "[TRACE] data_labels=I02 trace_function=1 ";
    if (qi::phrase_parse(content.begin(), content.end(), lit("[TRACE]") >> data_labels >> trace_function, asc::space)) {
        cout << "000000000000" << endl;
    }

    content = "[TRACE] "
            "data_labels=CLOCK 0 "
            "trace_function=3 "
            "drawtrace=TRUE "
            "[TRACE_DATA] "
            "9.800000e-022 9.800000e-022 9.800000e-022 9.800000e-022 9.800000e-022 "
            "9.800000e-022 9.800000e-022 9.800000e-022 9.800000e-022 9.800000e-022 "
            "9.800000e-022 9.800000e-022 9.800000e-022 9.800000e-022 9.800000e-022 "
            "9.800000e-022 9.800000e-022 9.800000e-022 9.800000e-022 9.800000e-022 "
            "[#TRACE_DATA] "
            "[#TRACE]";
    qi::rule<std::string::iterator, Trace(), asc::space_type> trace;
    trace %= lit("[TRACE]") >> data_labels >> trace_function >> drawtrace >> +trace_data >> lit("[#TRACE]");
    Trace val5;
    if ( qi::phrase_parse(content.begin(), content.end(), trace, asc::space, val5) ) {
        cout << "trace match" << endl;
    }



    return 0;
}

