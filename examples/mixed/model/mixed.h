#ifndef MIXED_H
#define MIXED_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "mixedIncludes.h"
#include "mixedEncoders.h"

// GENERATED_CODE_PARAM --block=mixed
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "mixedBase.h"
#include "mixedIncludes.h"
#include "mixedBlockCIncludes.h"
//contained instances forward class declaration
class blockABase;
class apbDecodeBase;
class blockCBase;
class blockBBase;

SC_MODULE(mixed), public blockBase, public mixedBase
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("mixed_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<mixed>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:
    // channels
    // An interface for A
    req_ack_channel< aSt, aASt > aStuffIf;
    // An interface for C
    rdy_vld_channel< seeSt > cStuffIf;
    // A start done interface
    notify_ack_channel< > startDone;
    // Duplicate interface def
    rdy_vld_channel< seeSt > dupIf;
    // CPU access to SoC registers in the design
    apb_channel< apbAddrSt, apbDataSt > apb_uBlockA;
    // CPU access to SoC registers in the design
    apb_channel< apbAddrSt, apbDataSt > apb_uBlockB;

    //instances contained in block
    std::shared_ptr<blockABase> uBlockA;
    std::shared_ptr<apbDecodeBase> uAPBDecode;
    std::shared_ptr<blockCBase> uBlockC;
    std::shared_ptr<blockBBase> uBlockB;

    mixed(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~mixed() override = default;

    // GENERATED_CODE_END
    // block implementation members
   
};

#endif //MIXED_H
