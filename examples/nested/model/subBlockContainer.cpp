// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE


// GENERATED_CODE_PARAM --block=subBlockContainer
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "subBlockContainer.h"
#include "subBlock_base.h"
SC_HAS_PROCESS(subBlockContainer);

subBlockContainer::registerBlock subBlockContainer::registerBlock_; //register the block with the factory

subBlockContainer::subBlockContainer(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("subBlockContainer", name(), bbMode)
        ,subBlockContainerBase(name(), variant)
        ,test("subBlock_test", "subBlock")
        ,uSubBlock0(std::dynamic_pointer_cast<subBlockBase>( instanceFactory::createInstance(name(), "uSubBlock0", "subBlock", "")))
        ,uSubBlock1(std::dynamic_pointer_cast<subBlockBase>( instanceFactory::createInstance(name(), "uSubBlock1", "subBlock", "")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uSubBlock0->dst(in);
    uSubBlock1->src(out);
    // instance to instance connections via channel
    uSubBlock0->src(test);
    uSubBlock1->dst(test);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
}

