#ifndef NESTEDL4_H
#define NESTEDL4_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=nestedL4
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
import nestedL4.base;
#include "rdy_vld_channel.h"
import nested;
using namespace nested_ns;
//contained instances base module imports
import nestedL5.base;

SC_MODULE(nestedL4), public blockBase, public nestedL4Base
{
private:

public:
    //instances contained in block
    std::shared_ptr<nestedL5Base> uNestedL5;

    nestedL4(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~nestedL4() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

#endif //NESTEDL4_H
