#ifndef IP_TOP_TANDEM_H
#define IP_TOP_TANDEM_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip_top
// GENERATED_CODE_BEGIN --template=testbench --section=header
#include "systemc.h"
#include "instanceFactory.h"

import ip_test_ip_top.base;
import common_shared_types;
using namespace common_shared_types_ns;
import ip_test_ip_top;
using namespace ip_test_ip_top_ns;
import ip_test_src;
using namespace ip_test_src_ns;
import ip;
using namespace ip_ns;
import ipBridge;
using namespace ipBridge_ns;
#include "ip_topExternal.h"

class ip_topTestbench: public sc_module, public blockBase, public ip_topChannels {

public:

    std::shared_ptr<ip_topBase> ip_top;
    ip_topExternal external;

    ip_topTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ip_topTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END

#endif /* IP_TOP_TANDEM_H */
