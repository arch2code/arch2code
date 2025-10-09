#ifndef NESTEDL1_H
#define NESTEDL1_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=nestedL1
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "nestedL1_base.h"
#include "nestedTopIncludes.h"
//contained instances forward class declaration
class nestedL2Base;

SC_MODULE(nestedL1), public blockBase, public nestedL1Base
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("nestedL1_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<nestedL1>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:
    //instances contained in block
    std::shared_ptr<nestedL2Base> uNestedL2;

    nestedL1(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~nestedL1() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

#endif //NESTEDL1_H
