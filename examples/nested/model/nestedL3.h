#ifndef NESTEDL3_H
#define NESTEDL3_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=nestedL3
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "nestedL3_base.h"
#include "nestedTopIncludes.h"
//contained instances forward class declaration
class nestedL4Base;

SC_MODULE(nestedL3), public blockBase, public nestedL3Base
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("nestedL3_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<nestedL3>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:
    //instances contained in block
    std::shared_ptr<nestedL4Base> uNestedL4;

    nestedL3(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~nestedL3() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

#endif //NESTEDL3_H
