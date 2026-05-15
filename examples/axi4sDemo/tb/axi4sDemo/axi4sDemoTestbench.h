#ifndef AXI4SDEMO_TANDEM_H
#define AXI4SDEMO_TANDEM_H
// 

// GENERATED_CODE_PARAM --block=axi4sDemo
// GENERATED_CODE_BEGIN --template=testbench --section=header
#include "systemc.h"
#include "instanceFactory.h"

#include "axi4sDemoBase.h"
#include "axi4sDemoExternal.h"

// Force-link function (active modules-mode anchor) for the testbench
// class. Referencing this symbol pulls the registration TU into static links.
void force_link_axi4sDemoTestbench();

class axi4sDemoTestbench: public sc_module, public blockBase, public axi4sDemoChannels {

public:

    std::shared_ptr<axi4sDemoBase> axi4sDemo;
    axi4sDemoExternal external;

    axi4sDemoTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~axi4sDemoTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END

#endif /* AXI4SDEMO_TANDEM_H */
