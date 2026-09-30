#ifndef INSTANCE_FACTORY_H
#define INSTANCE_FACTORY_H
//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include <functional>
#include <map>
#include <string>
#include <tuple>
#include <memory>

#include "blockBase.h"

// Generated non-templated block .cpp files (and generated testbench .cpp
// files) self-register with the instanceFactory through a namespace-scope
// static initializer. A2C_REGISTRATION_RETAIN marks the static so it survives
// compiler dead-code elimination ('used') and the linker's --gc-sections pass
// ('retain').
//
// This attribute does NOT make registration reachable when a block is packaged
// into a static archive: no source-level attribute can override the linker's
// archive-extraction rule (no symbol reference -> no extraction). A project
// that ships blocks as static archives must link those archives with
// -Wl,--whole-archive (or the platform equivalent), or add an explicit
// -Wl,-u <anchor> reference.
#if defined(__GNUC__) || defined(__clang__)
#define A2C_REGISTRATION_RETAIN [[gnu::used, gnu::retain]]
#else
#define A2C_REGISTRATION_RETAIN
#endif

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
    // projectName is the assembling project's, so the same (blockType, variant)
    // reused by two distinct assembler projects lands under distinct keys.
    static void registerBlock(std::string blockType, blockFactoryFunctionType blockFactoryFunction, std::string variant, std::string projectName);
    // allow top level to create mappings from instance names to block types prior to enumeration of model
    static void registerInstance(std::string instance, std::string blockType);
    static std::shared_ptr< blockBase> getInstance(std::string qualifiedName);
    static std::shared_ptr< blockBase > createTestBench(const char * testBench, const char * projectName);
    // projectName-qualified lookup: the lookup projectName must match the
    // projectName used at registerBlock time (both emitted by the same project).
    //
    // containerSuppliedFactory is the constructor a CONTAINER supplies for a
    // child whose Config is a function of the container's own Config. Such a
    // child is a FAMILY of C++ types, one per Config the container is
    // instantiated at, and the key carries no Config dimension, so no
    // registration made ahead of time can name the member this site needs.
    static std::shared_ptr< blockBase > createInstance(const char * hierarchy, const char * blockName, const char * blockTypeUser, const char * variant, const char * projectName, blockFactoryFunctionType containerSuppliedFactory = nullptr);
    static std::shared_ptr< blockBase > createInstance(const char * hierarchy, const char * blockName, const char * blockTypeUser, instanceFactoryMode inst, const char * variant, const char * projectName, blockFactoryFunctionType containerSuppliedFactory = nullptr);
    // Container-typed child construction. `Impl` is the child's implementation
    // class at the Config the container resolves for it, which the container
    // already spells in the dynamic_pointer_cast wrapping this call. The
    // mode-carrying form serves a tandem wrapper, itself a class template at a
    // known Config, asking for its own halves.
    template<typename Impl>
    static std::shared_ptr< blockBase > createInstance(const char * hierarchy, const char * blockName, const char * blockTypeUser, instanceFactoryMode inst, const char * variant, const char * projectName)
    {
        return createInstance(hierarchy, blockName, blockTypeUser, inst, variant, projectName,
            [](const char * name, const char * variantArg, blockBaseMode bbMode) -> std::shared_ptr< blockBase > {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<Impl>(name, variantArg, bbMode));
            });
    }
    template<typename Impl>
    static std::shared_ptr< blockBase > createInstance(const char * hierarchy, const char * blockName, const char * blockTypeUser, const char * variant, const char * projectName)
    {
        return createInstance<Impl>(hierarchy, blockName, blockTypeUser, INSTANCE_FACTORY_DEFAULT, variant, projectName);
    }
    static void setInstanceFactoryMode(instanceFactoryMode mode, std::string name);
    static bool isTandemMode(void);
    static void setTimed(int nsec, bool all, timedDelayMode mode);
    static void setLogging(verbosity_e verbosity);
    static std::string dumpInstances(void);
    // de-tandemise provided name and remove any extra hierarchy levels
    static std::string getHierarchyName(const std::string name, blockBaseMode bbMode);
private:
    // The variant string identifies the Config policy unambiguously under
    // variant ≅ Config within one project; the empty variant covers blocks with
    // no declared variants. Empty projectName is the unqualified/framework case.
    struct Key {
        std::string blockType;
        std::string variant;
        std::string projectName;
        bool operator<(const Key & rhs) const {
            return std::tie(blockType, variant, projectName) <
                   std::tie(rhs.blockType, rhs.variant, rhs.projectName);
        }
    };
    // map[Key] = function to create block of type Key.blockType
    // this map is used to instanitate blocks
    static std::map<Key, blockFactoryFunctionType >& getMap();
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
    static std::vector<std::pair<std::string, std::string>> & getRemapStrings();
    static std::string getQualName(const std::string name) {return testBenchQualStr + name;};
};
#endif //INSTANCE_FACTORY_H
