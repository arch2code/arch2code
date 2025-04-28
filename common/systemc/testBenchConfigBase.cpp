//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "q_assert.h"

#include "testBenchConfigBase.h"



void testBenchConfigBase::addParam(std::string name, uint64_t value)
{
    getParamMap().emplace(name, value);
}
void testBenchConfigBase::addParam(const std::initializer_list<std::pair<std::string, uint64_t> > & params)
{
    for(auto & p : params) {
        getParamMap().emplace(p.first, p.second);
    }
}
uint64_t testBenchConfigBase::getParam(std::string name, uint64_t defaultValue)
{
    auto it = getParamMap().find(name);
    if(it != getParamMap().end()) {
        return it->second;
    }
    return defaultValue;
}

uint64_t testBenchConfigBase::getParam(std::string name)
{
    auto it = getParamMap().find(name);
    if(it != getParamMap().end()) {
        return it->second;
    }
    return 0;
}

std::map<std::string, uint64_t >& testBenchConfigBase::getParamMap()
{
    static std::map<std::string, uint64_t> map;
    return map;
}

bool testBenchConfigBase::isValidParam(std::string name)
{
    auto it = getParamMap().find(name);
    return it != getParamMap().end();
}