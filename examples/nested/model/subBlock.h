#ifndef SUBBLOCK_H
#define SUBBLOCK_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include "systemc.h"


// GENERATED_CODE_PARAM --block=subBlock
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "subBlock_base.h"
#include "nestedTopIncludes.h"

SC_MODULE(subBlock), public blockBase, public subBlockBase
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("subBlock_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<subBlock>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:

    // channels


    subBlock(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~subBlock() override = default;

// GENERATED_CODE_END

    void forwarder(void);

    // block implementation members
};


#endif  //SUBBLOCK_H