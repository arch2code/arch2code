#ifndef TOP_H
#define TOP_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=top
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "top_base.h"
#include "nestedTopIncludes.h"
//contained instances forward class declaration
class testContainerBase;
class nestedL1Base;

SC_MODULE(top), public blockBase, public topBase
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("top_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<top>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:
    // channels
    // Test interface
    rdy_vld_channel< test_st > test;

    //instances contained in block
    std::shared_ptr<testContainerBase> uTestTop;
    std::shared_ptr<nestedL1Base> uNestedL1;

    top(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~top() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

#endif //TOP_H
