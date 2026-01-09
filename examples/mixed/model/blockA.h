#ifndef BLOCKA_H
#define BLOCKA_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "mixedIncludes.h"

// GENERATED_CODE_PARAM --block=blockA
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "blockABase.h"
#include "addressMap.h"
#include "hwRegister.h"
#include "hwMemory.h"
#include "mixedIncludes.h"
#include "mixedBlockCIncludes.h"
#include "mixedIncludeIncludes.h"

SC_MODULE(blockA), public blockBase, public blockABase
{
private:
    void regHandler(void);
    addressMap regs;

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("blockA_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<blockA>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:

    //registers
    hwRegister< aRegSt, 4 > roA; // A Read Only register

    // Local memory register infrastructure
    memory_channel< bSizeSt, aRegSt > blockATableLocal_channel;
    memory_out< bSizeSt, aRegSt > blockATableLocal_port;
    hwMemoryPort< bSizeSt, aRegSt > blockATableLocal_adapter;

    blockA(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockA() override = default;

    // GENERATED_CODE_END
    // block implementation members
    std::vector<aRegSt> blockATableLocal_shadow_;  // Shadow storage for local memory register
    void startTest(void);
    void blockATableLocalModel(void);  // Service thread for local memory register
};

#endif //BLOCKA_H
