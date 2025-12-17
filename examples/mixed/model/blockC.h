#ifndef BLOCKC_H
#define BLOCKC_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "mixedIncludes.h"

// GENERATED_CODE_PARAM --block=blockC
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "blockCBase.h"
#include "mixedBlockCIncludes.h"

SC_MODULE(blockC), public blockBase, public blockCBase
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("blockC_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<blockC>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:

    blockC(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockC() override = default;

    // GENERATED_CODE_END
    // block implementation members
   
};

#endif //BLOCKC_H
