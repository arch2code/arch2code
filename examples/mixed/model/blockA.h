#ifndef BLOCKA_H
#define BLOCKA_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "mixedIncludes.h"

// GENERATED_CODE_PARAM --block=blockA
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "blockA_base.h"
#include "addressMap.h"
#include "hwRegister.h"
#include "mixedIncludes.h"
#include "mixedBlockCIncludes.h"

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

    blockA(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockA() override = default;

    // GENERATED_CODE_END
    // block implementation members
    void startTest(void);
};

#endif //BLOCKA_H
