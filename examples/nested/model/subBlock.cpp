// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE



// GENERATED_CODE_PARAM --block=subBlock
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "subBlock.h"
SC_HAS_PROCESS(subBlock);

subBlock::registerBlock subBlock::registerBlock_; //register the block with the factory

subBlock::subBlock(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("subBlock", name(), bbMode)
        ,subBlockBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(forwarder)
}

// this module just takes data from the input and sends it to the output
void subBlock::forwarder()
{
    test_st data;
    data.a = 0;
    wait(SC_ZERO_TIME);
    while (true)
    {
        dst->read(data);
        std::cout << "write " << this->name() << " " << data.a << endl;
        src->write(data);
    }
}

