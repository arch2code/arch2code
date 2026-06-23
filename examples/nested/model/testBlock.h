#ifndef TESTBLOCK_H
#define TESTBLOCK_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"


// GENERATED_CODE_PARAM --block=testBlock
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "testBlockBase.h"

SC_MODULE(testBlock), public blockBase, public testBlockBase
{
private:

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

