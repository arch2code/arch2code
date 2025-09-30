#ifndef SUBBLOCKCONTAINER_H
#define SUBBLOCKCONTAINER_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"


// GENERATED_CODE_PARAM --block=subBlockContainer
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "subBlockContainer_base.h"
#include "nestedTopIncludes.h"
//contained instances forward class declaration
class subBlockBase;

SC_MODULE(subBlockContainer), public blockBase, public subBlockContainerBase
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("subBlockContainer_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<subBlockContainer>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:
    // channels
    // Test interface
    rdy_vld_channel< test_st > test;

    //instances contained in block
    std::shared_ptr<subBlockBase> uSubBlock0;
    std::shared_ptr<subBlockBase> uSubBlock1;

    subBlockContainer(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~subBlockContainer() override = default;

    // GENERATED_CODE_END

    // block implementation members
   
};

#endif //SUBBLOCKCONTAINER_H

