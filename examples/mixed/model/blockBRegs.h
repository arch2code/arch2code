#ifndef BLOCKBREGS_H
#define BLOCKBREGS_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=blockBRegs
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "blockBRegs_base.h"
#include "addressMap.h"
#include "hwRegister.h"
#include "mixedIncludes.h"
#include "mixedBlockCIncludes.h"
#include "mixedIncludeIncludes.h"

SC_MODULE(blockBRegs), public blockBase, public blockBRegsBase
{
private:
    void regHandler(void);
    addressMap regs;

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("blockBRegs_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<blockBRegs>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:

    // channels


    //registers
    hwRegister< dRegSt, 4 > rwD; // A Read Write register
    hwRegister< bSizeRegSt, 4 > roBsize; // A Read Only register with a structure that has a definition from an included context

    blockBRegs(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockBRegs() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

#endif //BLOCKBREGS_H
