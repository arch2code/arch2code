#ifndef NESTEDL2_H
#define NESTEDL2_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=nestedL2
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "nestedL2_base.h"
//contained instances forward class declaration
class nestedL3Base;

SC_MODULE(nestedL2), public blockBase, public nestedL2Base
{
private:

public:
    //instances contained in block
    std::shared_ptr<nestedL3Base> uNestedL3;

    nestedL2(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~nestedL2() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

#endif //NESTEDL2_H
