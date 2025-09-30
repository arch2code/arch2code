//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

// GENERATED_CODE_PARAM --block=nestedL2
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "nestedL2.h"
#include "nestedL3_base.h"
SC_HAS_PROCESS(nestedL2);

nestedL2::registerBlock nestedL2::registerBlock_; //register the block with the factory

nestedL2::nestedL2(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("nestedL2", name(), bbMode)
        ,nestedL2Base(name(), variant)
        ,uNestedL3(std::dynamic_pointer_cast<nestedL3Base>( instanceFactory::createInstance(name(), "uNestedL3", "nestedL3", "")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uNestedL3->nested3(nested2);
    log_.logPrint(fmt::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

