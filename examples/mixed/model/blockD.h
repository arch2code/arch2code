#ifndef BLOCKD_H
#define BLOCKD_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=blockD
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "blockDBase.h"
#include "mixedBlockCIncludes.h"
#include "mixedIncludes.h"
#include "mixedIncludeIncludes.h"

SC_MODULE(blockD), public blockBase, public blockDBase
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("blockD_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<blockD>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:

    blockD(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockD() override = default;

    // GENERATED_CODE_END
    // block implementation members
   
};

#endif //BLOCKD_H
