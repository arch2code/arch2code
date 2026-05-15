#ifndef BLOCKA_H
#define BLOCKA_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=blockA
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "blockABase.h"
#include "addressMap.h"
#include "hwRegister.h"
#include "hwMemory.h"
import mixed;
using namespace mixed_ns;
import mixedInclude;
using namespace mixedInclude_ns;

SC_MODULE(blockA), public blockBase, public blockABase
{
private:
    void regHandler(void);
    addressMap regs;

public:

    //registers
    hwRegister< aRegSt, 4 > roA; // A Read Only register

    //local memory register infrastructure
    memory_channel< bSizeSt, aRegSt > blockATableLocal_channel;
    memory_out< bSizeSt, aRegSt > blockATableLocal_port;
    hwMemoryPort< bSizeSt, aRegSt > blockATableLocal_adapter;
    memory_channel< bSizeSt, test37BitRegSt > blockATable37Bit_channel;
    memory_out< bSizeSt, test37BitRegSt > blockATable37Bit_port;
    hwMemoryPort< bSizeSt, test37BitRegSt > blockATable37Bit_adapter;

    blockA(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockA() override = default;

    // GENERATED_CODE_END
    // block implementation members
    std::vector<aRegSt> blockATableLocal_shadow_;  // Shadow storage for local memory register
    std::vector<test37BitRegSt> blockATable37Bit_shadow_;  // Shadow storage for 37-bit memory register
    void startTest(void);
    void blockATableLocalModel(void);  // Service thread for local memory register
    void blockATable37BitModel(void);  // Service thread for 37-bit memory register
};

#endif //BLOCKA_H
