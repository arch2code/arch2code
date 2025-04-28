#ifndef SECONDSUBB_H
#define SECONDSUBB_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include "systemc.h"


// GENERATED_CODE_PARAM --block=secondSubB
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "secondSubB_base.h"
#include "nestedTopIncludes.h"

SC_MODULE(secondSubB), public blockBase, public secondSubBBase
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("secondSubB_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<secondSubB>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:

    // channels


    secondSubB(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~secondSubB() override = default;

// GENERATED_CODE_END

    void forwarder(void);

    // block implementation members
};


#endif  //SECONDSUBB_H