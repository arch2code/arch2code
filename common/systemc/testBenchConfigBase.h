#ifndef TESTBENCH_CONFIG_BASE_H
#define TESTBENCH_CONFIG_BASE_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include <string>
#include <boost/program_options.hpp>
#include "logging.h"

namespace po = boost::program_options;

// based class for defining testBench configuration
struct testBenchConfigBase
{
public:

public:
    testBenchConfigBase() {};
    virtual ~testBenchConfigBase() = default; // Virtual Destructor
    // allow testBench to add command line options
    virtual void addProgramOptions(po::options_description &options) {};
    // process any testBench specific command line options, return false if error
    virtual bool handleProgramOptions(po::variables_map &vm) { return true;};
    // perform any testBench specific deinitialization
    virtual void final(void) { errorCode::pass(); };
    // print any testBench specific messages at end of test
    virtual void exitSummary(void) {};
    // create the testBench
    virtual bool createTestBench(void) = 0;
    virtual bool isDefaultTestBench(void) { return false; };
    
    static void addParam(const std::initializer_list<std::pair<std::string, uint64_t> > & params);
    static void addParam(std::string name, uint64_t value);
    static uint64_t getParam(std::string name, uint64_t defaultValue);
    static uint64_t getParam(std::string name);
    static bool isValidParam(std::string name);
private:
    static std::map<std::string, uint64_t >& getParamMap();

};

#include <type_traits>

// Primary template: if T does not have isDefaultTestBench, default to false.
template<typename T, typename = void>
struct default_marker_trait {
    static constexpr bool value = false;
};

// Specialization: if T::isDefaultTestBench exists, use its value.
template<typename T>
struct default_marker_trait<T, std::void_t<decltype(T::isDefaultTestBench)>> {
    static constexpr bool value = T::isDefaultTestBench;
};

// Convenience variable template (C++14 and later)
template<typename T>
constexpr bool is_default_testbench_v = default_marker_trait<T>::value;

#endif //(TESTBENCH_CONFIG_BASE_H)
