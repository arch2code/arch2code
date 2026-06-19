#ifndef NESTEDL6_H
#define NESTEDL6_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=nestedL6
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "nestedL6_base.h"

SC_MODULE(nestedL6), public blockBase, public nestedL6Base
{
private:

public:

    nestedL6(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~nestedL6() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

#endif //NESTEDL6_H
