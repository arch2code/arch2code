#ifndef NESTEDL6_H
#define NESTEDL6_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=nestedL6
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "nestedL6_base.h"
#include "nestedTopIncludes.h"

SC_MODULE(nestedL6), public blockBase, public nestedL6Base
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("nestedL6_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<nestedL6>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:

    nestedL6(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~nestedL6() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

#endif //NESTEDL6_H
