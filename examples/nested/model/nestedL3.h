#ifndef NESTEDL3_H
#define NESTEDL3_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=nestedL3
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "nestedL3Base.h"
//contained instances forward class declaration
class nestedL4Base;

SC_MODULE(nestedL3), public blockBase, public nestedL3Base
{
private:

public:
    //instances contained in block
    std::shared_ptr<nestedL4Base> uNestedL4;

    nestedL3(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~nestedL3() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

#endif //NESTEDL3_H
