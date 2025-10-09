#ifndef BLOCKF_H
#define BLOCKF_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=blockF
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "blockF_base.h"
#include "addressMap.h"
#include "hwMemory.h"
#include "mixedBlockCIncludes.h"
#include "mixedIncludes.h"

SC_MODULE(blockF), public blockBase, public blockFBase
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // Register parameter variants with factory
            instanceFactory::addParam({
                { "blockF.variant0.bob", BOB0 },
                { "blockF.variant0.fred", 0 },
                { "blockF.variant1.bob", BOB1 },
                { "blockF.variant1.fred", 1 },
            });
            // lamda function to construct the block
            instanceFactory::registerBlock("blockF_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<blockF>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:

    memories mems;
    //memories
    hwMemory< seeSt > test;

    blockF(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockF() override = default;
    void setTimed(int nsec, timedDelayMode mode) override
    {
        blockFBase::setTimed(nsec, mode);
        mems.setTimed(nsec, mode);
    }

    // GENERATED_CODE_END
    // block implementation members

};

#endif //BLOCKF_H
