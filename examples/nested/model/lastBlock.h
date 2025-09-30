#ifndef LASTBLOCK_H
#define LASTBLOCK_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include "systemc.h"


// GENERATED_CODE_PARAM --block=lastBlock
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "lastBlock_base.h"
#include "nestedTopIncludes.h"

SC_MODULE(lastBlock), public blockBase, public lastBlockBase
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("lastBlock_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<lastBlock>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:

    lastBlock(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~lastBlock() override = default;

// GENERATED_CODE_END

    void forwarder(void);

    // block implementation members
};


#endif  //LASTBLOCK_H