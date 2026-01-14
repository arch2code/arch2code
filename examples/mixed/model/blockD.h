#ifndef BLOCKD_H
#define BLOCKD_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=blockD
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "blockDBase.h"
#include "mixedIncludes.h"
#include "mixedBlockCIncludes.h"
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
    void memoryTest(void);
    
    // Memory register handler for blockBTableExt.
    // This services register accesses to blockBTableExt through the memory port.
    void blockBTableExtModel(void);
    std::vector<seeSt> blockBTableExt_shadow_;
    
    // Memory register handler for blockBTable37Bit.
    // This services register accesses to blockBTable37Bit through the memory port.
    void blockBTable37BitModel(void);
    std::vector<test37BitRegSt> blockBTable37Bit_shadow_;
};

#endif //BLOCKD_H
