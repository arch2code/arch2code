//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

// GENERATED_CODE_PARAM --block=nestedL1
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "nestedL1.h"
#include "nestedL2_base.h"
SC_HAS_PROCESS(nestedL1);

nestedL1::registerBlock nestedL1::registerBlock_; //register the block with the factory

nestedL1::nestedL1(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("nestedL1", name(), bbMode)
        ,nestedL1Base(name(), variant)
        ,uNestedL2(std::dynamic_pointer_cast<nestedL2Base>( instanceFactory::createInstance(name(), "uNestedL2", "nestedL2", "")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uNestedL2->nested2(nested1);
    log_.logPrint(fmt::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

