#ifndef NESTEDL5_H
#define NESTEDL5_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=nestedL5
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "nestedL5_base.h"
//contained instances forward class declaration
class nestedL6Base;

SC_MODULE(nestedL5), public blockBase, public nestedL5Base
{
private:

public:
    //instances contained in block
    std::shared_ptr<nestedL6Base> uNestedL6;

    nestedL5(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~nestedL5() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

#endif //NESTEDL5_H
