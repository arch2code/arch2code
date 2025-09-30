#ifndef NESTEDL4_H
#define NESTEDL4_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=nestedL4
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "nestedL4_base.h"
#include "nestedTopIncludes.h"
//contained instances forward class declaration
class nestedL5Base;

SC_MODULE(nestedL4), public blockBase, public nestedL4Base
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("nestedL4_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<nestedL4>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:
    //instances contained in block
    std::shared_ptr<nestedL5Base> uNestedL5;

    nestedL4(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~nestedL4() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

#endif //NESTEDL4_H
