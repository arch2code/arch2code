#ifndef SECONDSUBA_H
#define SECONDSUBA_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include "systemc.h"


// GENERATED_CODE_PARAM --block=secondSubA
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "secondSubA_base.h"
#include "nestedTopIncludes.h"

SC_MODULE(secondSubA), public blockBase, public secondSubABase
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("secondSubA_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<secondSubA>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:

    // channels


    secondSubA(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~secondSubA() override = default;

// GENERATED_CODE_END

    void forwarder(void);

    // block implementation members
};


#endif  //SECONDSUBA_H