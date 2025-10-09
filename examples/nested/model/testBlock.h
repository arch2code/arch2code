#ifndef TESTBLOCK_H
#define TESTBLOCK_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"


// GENERATED_CODE_PARAM --block=testBlock
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "testBlock_base.h"
#include "nestedTopIncludes.h"

SC_MODULE(testBlock), public blockBase, public testBlockBase
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("testBlock_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<testBlock>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:

    testBlock(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~testBlock() override = default;

    // GENERATED_CODE_END
    void producerLoop1();
    void producerLoop2();
    void consumerLoop1();
    void consumerLoop2();
    void producer(rdy_vld_out< test_st > &dataOut);
    void consumer(rdy_vld_in< test_st > &dataIn); 
    // block implementation members
    sc_event  *test1;
   
};

#endif //TESTBLOCK_H

