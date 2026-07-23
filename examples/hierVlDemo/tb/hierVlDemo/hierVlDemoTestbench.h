#ifndef AXI4SDEMO_TANDEM_H
#define AXI4SDEMO_TANDEM_H
// 

// GENERATED_CODE_PARAM --block=hierVlDemo
// GENERATED_CODE_BEGIN --template=testbench --section=header
#include "systemc.h"
#include "instanceFactory.h"

import hierVlDemo.base;
import hierVlDemo_tb;
using namespace hierVlDemo_tb_ns;
#include "hierVlDemoExternal.h"

class hierVlDemoTestbench: public sc_module, public blockBase, public hierVlDemoChannels {

public:

    std::shared_ptr<hierVlDemoBase> hierVlDemo;
    hierVlDemoExternal external;

    hierVlDemoTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~hierVlDemoTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END

#endif /* AXI4SDEMO_TANDEM_H */
