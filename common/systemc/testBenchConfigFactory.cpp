//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "q_assert.h"

#include "testBenchConfigFactory.h"

std::shared_ptr< testBenchConfigBase > testBenchConfigFactory::testBench = nullptr;
std::string testBenchConfigFactory::defaultTestBench = "";

void testBenchConfigFactory::registerTestBenchConfig(std::string testBenchName, testBenchConfigFactoryFunctionType factoryFunction, bool isDefault)
{
    if (isDefault) {
        defaultTestBench = testBenchName;
    }
    getMap().emplace(testBenchName, factoryFunction);
}
     
std::shared_ptr< testBenchConfigBase > testBenchConfigFactory::createTestBench(const std::string testBenchName)
{
    std::string testBenchLocal = testBenchName;
    if (testBenchName.empty()) {
        std::cout << "using default testBench " << defaultTestBench << std::endl;
        testBenchLocal = defaultTestBench;
    }
    auto map = getMap();
    auto it = map.find(testBenchLocal);
    if(it != map.end()) {
        testBench = it->second(testBenchLocal.c_str());
        return testBench;
    } else {
        if (testBenchLocal.empty()) {
            std::cout << "TestBench not set and no defaultTestBench" << std::endl;
        } else {
            std::cout << "TestBench " << testBenchLocal << " not found" << std::endl;
        }
        std::cout << "TestBenches available:" << std::endl;
        for (auto it2 = map.cbegin(); it2 != map.cend(); ++it2) {
            std::cout << "\t" << it2->first << std::endl;
        }
    }
    return nullptr;
}

std::map<std::string, testBenchConfigFactoryFunctionType >& testBenchConfigFactory::getMap()
{
    static std::map<std::string, testBenchConfigFactoryFunctionType> map;
    return map;
}

