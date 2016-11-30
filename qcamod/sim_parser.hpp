//
// Created by fpeng on 2016/11/30.
//

#ifndef QCADESIGNER_MOD_SIM_PARSER_H
#define QCADESIGNER_MOD_SIM_PARSER_H

#include <boost/spirit/include/qi.hpp>
#include <boost/spirit/include/karma.hpp>
#include <boost/spirit/include/phoenix_operator.hpp>
namespace qi    = boost::spirit::qi;
namespace karma = boost::spirit::karma;
namespace asc = boost::spirit::ascii;

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
};

template<typename Iterator>
struct SimParser : qi::grammar<Iterator, std::vector<Trace>(), asc::space_type> {

    SimParser() : SimParser::base_type(start) {

        using qi::int_;
        using qi::double_;
        using qi::lit;

        using qi::eps;

        using qi::_val;
        using qi::_1;

        using qi::lexeme;

        trace_data %= lit("[TRACE_DATA]") >> +double_>> lit("[#TRACE_DATA]");
        data_labels = eps[_val=""] >> lit("data_labels=") >> lexeme[+((~qi::space)[_val+=_1])] >> -(asc::digit[_val+=" ", _val+=_1]);
        trace_function %= lit("trace_function=") >> int_;
        drawtrace %= lit("drawtrace=") >> draw_trace_symbol;
        trace %= lit("[TRACE]") >> data_labels >> trace_function >> drawtrace >> +trace_data >> lit("[#TRACE]");
        start %= lit("[TRACES]") >> +trace >> lit("[#TRACES]");
    }

    qi::rule<Iterator, std::vector<double>(), asc::space_type> trace_data;
    qi::rule<Iterator, std::string(), asc::space_type> data_labels;
    qi::rule<Iterator, int(), asc::space_type> trace_function;
    qi::rule<Iterator, bool(), asc::space_type> drawtrace;
    qi::rule<Iterator, Trace(), asc::space_type> trace;
    qi::rule<Iterator, std::vector<Trace>(), asc::space_type> start;


    static DrawTraceSymbolTable draw_trace_symbol;

};//end template

template<typename Iterator>
DrawTraceSymbolTable SimParser<Iterator>::draw_trace_symbol;


template<typename Iterator>
int parse_sim_file_by_spirit(Iterator first, Iterator last, std::vector<Trace> &traces) {
    SimParser<Iterator> parser;
    qi::phrase_parse(first, last, parser, asc::space, traces);
}

#endif //QCADESIGNER_MOD_SIM_PARSER_H
