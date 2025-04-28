#ifndef TESTBENCH_CONFIG_FACTORY_H
#define TESTBENCH_CONFIG_FACTORY_H
//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include <functional>
#include <map>
#include <string>
#include <memory>

#include "testBenchConfigBase.h"


// registration is performed via static structures in the testBench implementation files leveraging
// C++ static initialization methods. Note that code takes care of the static initialization order problems
typedef std::function< std::shared_ptr< testBenchConfigBase >(const char * testBenchName) > testBenchConfigFactoryFunctionType;
class testBenchConfigFactory
{
public:
    testBenchConfigFactory();
    // allow implementations to register thier constructors
    static void registerTestBenchConfig(std::string testBenchName, testBenchConfigFactoryFunctionType factoryFunction, bool isDefault=false);
    // allow top level to create mappings from instance names to testBench types prior to enumeration of model
    static std::shared_ptr< testBenchConfigBase > createTestBench(const std::string testBenchName);
    static std::shared_ptr< testBenchConfigBase > getTestBench(void) 
    {
        Q_ASSERT_CTX_NODUMP(testBench != nullptr, "", "TestBench not created"); 
        return testBench; 
    };
private:
    // map[testBenchType] = function to create testBench of type testBenchType
    // this map is used to instanitate testBenchs
    static std::map<std::string, testBenchConfigFactoryFunctionType >& getMap();
    static std::shared_ptr< testBenchConfigBase > testBench;
    static std::string defaultTestBench;
};
#endif //TESTBENCH_CONFIG_FACTORY_H
