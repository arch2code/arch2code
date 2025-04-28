#ifndef SECONDBLOCK_H
#define SECONDBLOCK_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include "systemc.h"


// GENERATED_CODE_PARAM --block=secondBlock
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "secondBlock_base.h"
#include "nestedTopIncludes.h"
//contained instances forward class declaration
class secondSubABase;
class secondSubBBase;

SC_MODULE(secondBlock), public blockBase, public secondBlockBase
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("secondBlock_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<secondBlock>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:

    // channels
    //   test
    rdy_vld_channel< test_st > test;

    //instances contained in block
    std::shared_ptr<secondSubABase> uSecondSubA;
    std::shared_ptr<secondSubBBase> uSecondSubB;

    secondBlock(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~secondBlock() override = default;

// GENERATED_CODE_END

    void forwarder(void);

    // block implementation members
};


#endif  //SECONDBLOCK_H