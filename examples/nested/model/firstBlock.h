#ifndef FIRSTBLOCK_H
#define FIRSTBLOCK_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include "systemc.h"


// GENERATED_CODE_PARAM --block=firstBlock
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "firstBlock_base.h"
#include "nestedTopIncludes.h"

SC_MODULE(firstBlock), public blockBase, public firstBlockBase
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("firstBlock_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<firstBlock>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:

    firstBlock(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~firstBlock() override = default;

// GENERATED_CODE_END

    void producer(void);
    void consumer(void);

    // block implementation members
};


#endif  //SUBBLOCK_H