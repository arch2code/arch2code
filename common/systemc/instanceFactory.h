#ifndef INSTANCE_FACTORY_H
#define INSTANCE_FACTORY_H
//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include <functional>
#include <map>
#include <string>
#include <memory>

#include "blockBase.h"

enum instanceFactoryMode { INSTANCE_FACTORY_DEFAULT, INSTANCE_FACTORY_PRIMARY_TYPE, INSTANCE_FACTORY_SECONDARY_TYPE };

// this file allows the controllable configuration of the model. All blocks must be registered with the instanceFactory
// if no exceptions are registered, then model implementations will be defaulted to. If exceptions are registered, then
// the instanceFactory will use the exceptions instead of the defaults. This allows for the creation of a model that
// is a mix of default and custom blocks. The custom blocks are typically verification blocks
// registration is performed via static structures in the block implementation files leveraging
// C++ static initialization methods. Note that code takes care of the static initialization order problems
typedef std::function< std::shared_ptr< blockBase >(const char * blockName, const char * variant, blockBaseMode bbMode) > blockFactoryFunctionType;
class instanceFactory
{
public:
    instanceFactory();
    static constexpr const char* testBenchStr = "tb";    
    static constexpr const char* testBenchQualStr = "tb.";    
    // allow implementation to register thier constructors
    static void registerBlock(std::string blockType, blockFactoryFunctionType blockFactoryFunction);
    // for variant specific initialization
    static void registerBlock(std::string blockType, blockFactoryFunctionType blockFactoryFunction, std::string variant);
    // allow top level to create mappings from instance names to block types prior to enumeration of model
    static void registerInstance(std::string instance, std::string blockType);
    static std::shared_ptr< blockBase> getInstance(std::string qualifiedName);
    static std::shared_ptr< blockBase > createTestBench(const char * testBench);
    static std::shared_ptr< blockBase > createInstance(const char * hierarchy, const char * blockName, const char * blockTypeUser, instanceFactoryMode inst);
    static std::shared_ptr< blockBase > createInstance(const char * hierarchy, const char * blockName, const char * blockTypeUser, const char * variant);
    static std::shared_ptr< blockBase > createInstance(const char * hierarchy, const char * blockName, const char * blockTypeUser, instanceFactoryMode inst, const char * variant);
    static void setInstanceFactoryMode(instanceFactoryMode mode, std::string name);
    static bool isTandemMode(void);
    static void setTimed(int nsec, bool all, timedDelayMode mode);
    static void setLogging(verbosity_e verbosity);
    static void addParam(const std::initializer_list<std::pair<std::string, uint64_t> > & params);
    static void addParam(std::string name, uint64_t value);
    static uint64_t getParam(const char * blockName, const std::string variant, std::string param);
    static std::string dumpInstances(void);
    // de-tandemise provided name and remove any extra hierarchy levels
    static std::string getHierarchyName(const std::string name, blockBaseMode bbMode);
private:
    // map[blockType] = function to create block of type blockType
    // this map is used to instanitate blocks
    static std::map<std::string, blockFactoryFunctionType >& getMap();
    // map[instanceName] = blockType
    // this contains any special case mappings where the instance is not of default type
    static std::map<std::string, std::string>& getInstMap();
    // map[qualifiedName] = instance
    // this contains pointers to the instances that have been created
    static std::map<std::string, std::shared_ptr< blockBase> >& getObjectMap();
    // vec[type] = typeString
    // this contains pointers to the instances that have been created
    static std::vector<std::string> & getInstanceModeString();
    static bool & tandemMode();
    static std::map<std::string, uint64_t> & getVariantParams();
    static std::vector<std::pair<std::string, std::string>> & getRemapStrings();
    static std::string getQualName(const std::string name) {return testBenchQualStr + name;};
};
#endif //INSTANCE_FACTORY_H
