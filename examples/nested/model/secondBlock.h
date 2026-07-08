#ifndef SECONDBLOCK_H
#define SECONDBLOCK_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
#include "systemc.h"


// GENERATED_CODE_PARAM --block=secondBlock
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
import secondBlock.base;
#include "rdy_vld_channel.h"
import nested;
using namespace nested_ns;
//contained instances base module imports
import secondSubA.base;
import secondSubB.base;

SC_MODULE(secondBlock), public blockBase, public secondBlockBase
{
private:

public:
    // channels
    // Test interface
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