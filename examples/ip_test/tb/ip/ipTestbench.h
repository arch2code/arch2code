#ifndef IP_TESTBENCH_H
#define IP_TESTBENCH_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip --variant=variant0
// GENERATED_CODE_BEGIN --template=testbench --section=header
#include "systemc.h"
#include "instanceFactory.h"

#include "ipBase.h"
#include "ipExternal.h"

// Force-link function (active modules-mode anchor) for the testbench
// class. Referencing this symbol pulls the registration TU into static links.
void force_link_ipTestbench();

class ipTestbench: public sc_module, public blockBase, public ipChannels<ipVariant0Config> {

public:

    std::shared_ptr<ipBase<ipVariant0Config>> ip;
    ipExternal external;

    ipTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ipTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END

#endif /* IP_TESTBENCH_H */
