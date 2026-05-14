//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "q_assert.h"
#include <array>
#include <format>


#include "instanceFactory.h"



void instanceFactory::registerBlock(std::string blockType, blockFactoryFunctionType blockFactoryFunction)
{
    registerBlock(std::move(blockType), std::move(blockFactoryFunction), std::string{});
}
    // for variant specific initialization
void instanceFactory::registerBlock(std::string blockType, blockFactoryFunctionType blockFactoryFunction, std::string variant)
{
    getMap().emplace(Key{std::move(blockType), std::move(variant)}, std::move(blockFactoryFunction));
}
// allow top level to create mappings from instance names to block types prior to enumeration of model
void instanceFactory::registerInstance(std::string instance, std::string blockType)
{
    if (blockType == "tandem") {
        // someone declared a tandem block, so we are in tandem mode
        tandemMode() = true;
    }
    getInstMap().emplace(getQualName(instance), blockType);
}
std::shared_ptr< blockBase> instanceFactory::getInstance(std::string qualifiedName)
{
    std::array<std::string, 2> candidates = {qualifiedName, getQualName(qualifiedName)};
    for (auto &candidate : candidates) {
        auto it = getObjectMap().find(candidate);
        if (it != getObjectMap().end()) {
            return it->second;
        }
    }
    Q_ASSERT_CTX_NODUMP(false, "", std::format("Unknown instance {} Check your command line option is a valid hierarchy name", qualifiedName) );
    return NULL;

}
// used to create the top level testbench of the model
std::shared_ptr< blockBase > instanceFactory::createTestBench(const char * testBench)
{
    return createInstance("", testBenchStr, testBench, INSTANCE_FACTORY_DEFAULT, "");
}
std::shared_ptr< blockBase > instanceFactory::createInstance(const char * hierarchy, const char * blockName, const char * blockTypeUser, instanceFactoryMode inst)
{
    return createInstance(hierarchy, blockName, blockTypeUser, inst, "");
}
std::shared_ptr< blockBase > instanceFactory::createInstance(const char * hierarchy, const char * blockName, const char * blockTypeUser, const char * variant)
{
    return createInstance(hierarchy, blockName, blockTypeUser, INSTANCE_FACTORY_DEFAULT, variant);
}
std::shared_ptr< blockBase > instanceFactory::createInstance(const char * hierarchy, const char * blockName, const char * blockTypeUser, instanceFactoryMode inst, const char * variant)
{
    // figure out what type of block to create for this instance
    std::string hierarchyStr(hierarchy);
    std::string qualifiedName = hierarchyStr.empty() ? std::string(blockName) : hierarchyStr + std::string(".") + std::string(blockName);
    std::string blockType;
    std::string instMode;
    verbosity_e verbosity = VERBOSITY_UNKNOWN;
    if (inst == INSTANCE_FACTORY_DEFAULT)
    {
        auto instIt = getInstMap().find(qualifiedName);
        if (instIt != getInstMap().end()) {
            instMode = instIt->second;
            blockType = std::string(blockTypeUser) + "_" + instIt->second;
        } else {
            // defaulting to blockTypeUser
            blockType = std::string(blockTypeUser) + std::string("_model");
        }
    } else {
        instMode = getInstanceModeString()[inst];
        blockType = std::string(blockTypeUser) + "_" + instMode;
    }
    // Lookup order:
    //   1. exact (blockType, variant)
    //   2. variant fallback (blockType, "")
    //   3. error
    for (const auto &candidateVariant : std::array<std::string, 2>{std::string(variant), std::string()}) {
        auto it = getMap().find(Key{blockType, candidateVariant});
        if (it != getMap().end()) {
            bool tandem = (inst != INSTANCE_FACTORY_DEFAULT);
            if (tandem) {
                // only get here for true tandem block
                getRemapStrings().emplace_back(qualifiedName, hierarchyStr);
            } else {
                std::string parent(hierarchyStr);
                while (parent.size() > 0) {
                    auto instIt = getInstMap().find(parent);
                    if (instIt != getInstMap().end()) {
                        if (instIt->second == "tandem") {
                            tandem = true; // inherit from a tandem block
                            break;
                        }
                    }
                    size_t pos = parent.find_last_of(".");
                    if (pos == std::string::npos)
                    {
                        parent = "";
                    } else {
                        parent = parent.substr(0, pos);
                    }
                }
            }
            auto newIt = getObjectMap().emplace(qualifiedName, nullptr);
            blockBaseMode bbMode = tandem ? BLOCKBASEMODE_TANDEM : BLOCKBASEMODE_NORMAL;
            std::shared_ptr< blockBase> newBlock = it->second(blockName, variant, bbMode);
            newIt.first->second = newBlock;
            if (verbosity != VERBOSITY_UNKNOWN) {
                newBlock->setLogging(verbosity);
            }
            if (tandem)
            {

            } else {
                // check if one of parent is a tandem block, as we want all the child blocks to be tandem
            }
            return newBlock;
        }
    }
    Q_ASSERT_CTX_NODUMP(false, "", std::format("Attempted to create an instance {} of an unregistered block type {}", blockName, blockType) );
    return NULL;
}
void instanceFactory::setInstanceFactoryMode(instanceFactoryMode mode, std::string name)
{
    getInstanceModeString()[mode] = name;
}
bool instanceFactory::isTandemMode(void)
{
    return tandemMode();
}
void instanceFactory::setTimed(int nsec, bool all, timedDelayMode mode)
{
    auto &instMap = getInstMap();
    auto &objMap = getObjectMap();
    bool isTandem = isTandemMode();
    std::string tandemPrimaryType;
    if (isTandem) {
        tandemPrimaryType = getInstanceModeString()[INSTANCE_FACTORY_PRIMARY_TYPE];
    }
    if (all) {
        for (auto it = getObjectMap().begin(); it != getObjectMap().end(); ++it) {
            it->second->setTimed(nsec, mode);
        }
    } else {
        for (auto it = instMap.begin(); it != instMap.end(); ++it) {
            std::string qualifiedName = it->first;
            std::string blockType = it->second;
            if (blockType == "tandem") {
                qualifiedName = qualifiedName + ".verif";  // modify to search for primary model block
                blockType = "model";
            }
            auto objIt = objMap.find(qualifiedName);
            // we end up looking for either non tandem model or tandem with primary model
            if (objIt != objMap.end()) {
                objIt->second->setTimed(nsec, mode);
            }
        }
    }
}
void instanceFactory::setLogging(verbosity_e verbosity)
{
    auto &instMap = getInstMap();
    auto &objMap = getObjectMap();
    bool isTandem = isTandemMode();
    std::string tandemPrimaryType;
    if (isTandem) {
        tandemPrimaryType = getInstanceModeString()[INSTANCE_FACTORY_PRIMARY_TYPE];
    }

        for (auto it = instMap.begin(); it != instMap.end(); ++it) {
            std::string qualifiedName = it->first;
            std::string blockType = it->second;
            std::vector<std::string> qualifiedNames{qualifiedName};
            if (blockType == "tandem") {
                qualifiedNames.push_back(qualifiedName + ".verif");
                qualifiedNames.push_back(qualifiedName + ".model");
            }
            for (auto &name : qualifiedNames) {
                auto objIt = objMap.find(name);
                // we end up looking for either non tandem model or tandem with primary model
                if (objIt != objMap.end()) {
                    objIt->second->setLogging(verbosity);
                    objIt->second->setBlockLogging(verbosity);
                }
            }
        }

}
std::string instanceFactory::dumpInstances(void)
{
    std::string ret;
    std::map<std::string, std::shared_ptr< blockBase>> &instMap = getObjectMap();
    for (auto it = instMap.begin(); it != instMap.end(); ++it) {
        ret += it->first + "\n";
    }
    std::vector<std::pair<std::string, std::string>> &remaps = getRemapStrings();
    for (auto it = remaps.begin(); it != remaps.end(); ++it) {
        ret += it->first + " remapped to " + it->second + "\n";
    }
    return ret;
}
// de-tandemise provided name and remove any extra hierarchy levels
std::string instanceFactory::getHierarchyName(const std::string name, blockBaseMode bbMode)
{
    if (bbMode == BLOCKBASEMODE_NOFACTORY) {
        return name;
    }
    auto remaps = getRemapStrings();
    std::string ret(name);
    for (auto it = remaps.begin(); it != remaps.end(); ++it) {
        // check if name starts with remap string
        if (name.find(it->first) == 0) {
            // it does so perform the remap
            ret = it->second + name.substr(it->first.size());
            break;
        }
    }
    // ret should now contain the name without any tandem hierarchy
    auto hierarchy = getObjectMap();
    while (ret.length() > 0) {
        if (hierarchy.find(ret) != hierarchy.end()) {
            return ret;
        }
        size_t pos = ret.find_last_of(".");
        if (pos == std::string::npos) {
            Q_ASSERT_CTX_NODUMP(false, "", std::format("Could not find instance name {}", name) );
        } else {
            ret = ret.substr(0, pos);
        }
    }
    Q_ASSERT_CTX_NODUMP(false, "", std::format("Could not find instance name {}", name) );
    return "";
}

// map[Key] = function to create block of type Key.blockType
// this map is used to instanitate blocks
std::map<instanceFactory::Key, blockFactoryFunctionType >& instanceFactory::getMap()
{
    static std::map<instanceFactory::Key, blockFactoryFunctionType> map;
    return map;
}
// map[instanceName] = blockType
// this contains any special case mappings where the instance is not of default type
std::map<std::string, std::string>& instanceFactory::getInstMap()
{
    static std::map<std::string, std::string> map;
    return map;
}
// map[qualifiedName] = instance
// this contains pointers to the instances that have been created
std::map<std::string, std::shared_ptr< blockBase> >& instanceFactory::getObjectMap()
{
    static std::map<std::string, std::shared_ptr< blockBase> > map;
    return map;
}
// vec[type] = typeString
// this contains pointers to the instances that have been created
std::vector<std::string> & instanceFactory::getInstanceModeString()
{
    static std::vector<std::string> vec = {"", "model", "model"}; // default type mappings for tandem model
    return vec;
}
bool & instanceFactory::tandemMode()
{
    static bool mode = false;
    return mode;
}
std::vector<std::pair<std::string, std::string>> & instanceFactory::getRemapStrings()
{
    static std::vector<std::pair<std::string, std::string>> remaps;
    return remaps;
}

