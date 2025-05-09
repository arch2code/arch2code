#ifndef TOP_H
#define TOP_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "mixedIncludes.h"
#include "mixedEncoders.h"

// GENERATED_CODE_PARAM --block=top
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "top_base.h"
#include "mixedIncludes.h"
#include "mixedBlockCIncludes.h"
//contained instances forward class declaration
class cpuBase;
class blockABase;
class apbDecodeBase;
class blockCBase;
class blockBBase;

SC_MODULE(top), public blockBase, public topBase
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("top_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<top>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:

    // channels
    //   aStuffIf
    req_ack_channel< aSt, aASt > aStuffIf;
    //   cStuffIf
    rdy_vld_channel< seeSt > cStuffIf;
    //   startDone
    notify_ack_channel< > startDone;
    //   apbReg
    apb_channel< apbAddrSt, apbDataSt > apb_uBlockA;
    //   apbReg
    apb_channel< apbAddrSt, apbDataSt > apb_uBlockB;
    //   apbReg
    apb_channel< apbAddrSt, apbDataSt > apbReg;

    //instances contained in block
    std::shared_ptr<blockABase> uBlockA;
    std::shared_ptr<blockCBase> uBlockC;
    std::shared_ptr<blockBBase> uBlockB;
    std::shared_ptr<apbDecodeBase> uAPBDecode;
    std::shared_ptr<cpuBase> uCPU;

    top(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~top() override = default;

    // GENERATED_CODE_END
    // block implementation members
   
};

#endif //TOP_H
