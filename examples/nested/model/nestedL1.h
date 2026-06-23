#ifndef NESTEDL1_H
#define NESTEDL1_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=nestedL1
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "nestedL1Base.h"
//contained instances forward class declaration
class nestedL2Base;

SC_MODULE(nestedL1), public blockBase, public nestedL1Base
{
private:

public:
    //instances contained in block
    std::shared_ptr<nestedL2Base> uNestedL2;

    nestedL1(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~nestedL1() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

#endif //NESTEDL1_H
