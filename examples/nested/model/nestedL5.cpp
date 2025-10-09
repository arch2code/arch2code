//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

// GENERATED_CODE_PARAM --block=nestedL5
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "nestedL5.h"
#include "nestedL6_base.h"
SC_HAS_PROCESS(nestedL5);

nestedL5::registerBlock nestedL5::registerBlock_; //register the block with the factory

nestedL5::nestedL5(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("nestedL5", name(), bbMode)
        ,nestedL5Base(name(), variant)
        ,uNestedL6(std::dynamic_pointer_cast<nestedL6Base>( instanceFactory::createInstance(name(), "uNestedL6", "nestedL6", "")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uNestedL6->nested6(nested5);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

