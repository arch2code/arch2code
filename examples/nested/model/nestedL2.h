#ifndef NESTEDL2_H
#define NESTEDL2_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=nestedL2
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "nestedL2_base.h"
#include "nestedTopIncludes.h"
//contained instances forward class declaration
class nestedL3Base;

SC_MODULE(nestedL2), public blockBase, public nestedL2Base
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("nestedL2_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<nestedL2>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:
    //instances contained in block
    std::shared_ptr<nestedL3Base> uNestedL3;

    nestedL2(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~nestedL2() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

#endif //NESTEDL2_H
