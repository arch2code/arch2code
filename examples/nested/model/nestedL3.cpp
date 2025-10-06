//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

// GENERATED_CODE_PARAM --block=nestedL3
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "nestedL3.h"
#include "nestedL4_base.h"
SC_HAS_PROCESS(nestedL3);

nestedL3::registerBlock nestedL3::registerBlock_; //register the block with the factory

nestedL3::nestedL3(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("nestedL3", name(), bbMode)
        ,nestedL3Base(name(), variant)
        ,uNestedL4(std::dynamic_pointer_cast<nestedL4Base>( instanceFactory::createInstance(name(), "uNestedL4", "nestedL4", "")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uNestedL4->nested4(nested3);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

