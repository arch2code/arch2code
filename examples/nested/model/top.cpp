//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

// GENERATED_CODE_PARAM --block=top
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "top.h"
#include "testContainer_base.h"
#include "nestedL1_base.h"
SC_HAS_PROCESS(top);

top::registerBlock top::registerBlock_; //register the block with the factory

top::top(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("top", name(), bbMode)
        ,topBase(name(), variant)
        ,test("nestedL1_test", "testContainer")
        ,uTestTop(std::dynamic_pointer_cast<testContainerBase>( instanceFactory::createInstance(name(), "uTestTop", "testContainer", "")))
        ,uNestedL1(std::dynamic_pointer_cast<nestedL1Base>( instanceFactory::createInstance(name(), "uNestedL1", "nestedL1", "")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    uTestTop->test(test);
    uNestedL1->nested1(test);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

