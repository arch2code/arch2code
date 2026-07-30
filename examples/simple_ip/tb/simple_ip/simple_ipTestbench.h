#ifndef SIMPLE_IP_TESTBENCH_H
#define SIMPLE_IP_TESTBENCH_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=simple_ip
// GENERATED_CODE_BEGIN --template=testbench --section=header
#include "systemc.h"
#include "instanceFactory.h"

import simple_ip.base;
import common_shared_types;
using namespace common_shared_types_ns;
import simple_ip;
using namespace simple_ip_ns;
import ip;
using namespace ip_ns;
#include "simple_ipExternal.h"

class simple_ipTestbench: public sc_module, public blockBase, public simple_ipChannels {

public:

    std::shared_ptr<simple_ipBase> simple_ip;
    simple_ipExternal external;

    simple_ipTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~simple_ipTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END

#endif /* SIMPLE_IP_TESTBENCH_H */
