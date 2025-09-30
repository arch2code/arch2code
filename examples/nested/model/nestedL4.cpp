//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

// GENERATED_CODE_PARAM --block=nestedL4
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "nestedL4.h"
#include "nestedL5_base.h"
SC_HAS_PROCESS(nestedL4);

nestedL4::registerBlock nestedL4::registerBlock_; //register the block with the factory

nestedL4::nestedL4(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("nestedL4", name(), bbMode)
        ,nestedL4Base(name(), variant)
        ,uNestedL5(std::dynamic_pointer_cast<nestedL5Base>( instanceFactory::createInstance(name(), "uNestedL5", "nestedL5", "")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uNestedL5->nested5(nested4);
    log_.logPrint(fmt::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

