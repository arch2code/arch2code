// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE



// GENERATED_CODE_PARAM --block=secondSubA
// GENERATED_CODE_BEGIN --template=constructor --section=init 
#include "secondSubA.h"
SC_HAS_PROCESS(secondSubA);

secondSubA::registerBlock secondSubA::registerBlock_; //register the block with the factory

secondSubA::secondSubA(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("secondSubA", name(), bbMode)
        ,secondSubABase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(fmt::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(forwarder)
}

// this module just takes data from the input and sends it to the output
void secondSubA::forwarder()
{
    test_st data;
    data.a = 0;
    wait(SC_ZERO_TIME);
    while (true)
    {
        primary->read(data);
        std::cout << "write " << this->name() << " " << data.a << endl;
        test->write(data);
    }
}

