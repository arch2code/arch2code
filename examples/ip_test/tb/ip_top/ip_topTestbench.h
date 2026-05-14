#ifndef IP_TOP_TANDEM_H
#define IP_TOP_TANDEM_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip_top
// GENERATED_CODE_BEGIN --template=testbench --section=header
#include "systemc.h"
#include "instanceFactory.h"

#include "ip_topBase.h"
#include "ip_topExternal.h"

// Force-link function (active modules-mode anchor) for the testbench
// class. See plan-block-registration.md "Force-Link Function".
void force_link_ip_topTestbench();

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
