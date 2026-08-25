#ifndef AXISOCKET_TESTBENCH_H
#define AXISOCKET_TESTBENCH_H
// 

// GENERATED_CODE_PARAM --block=axiSocket
// GENERATED_CODE_BEGIN --template=testbench --section=header
#include "systemc.h"
#include "instanceFactory.h"

import axiSocketMaster_axiSocket.base;
import axiSocketMaster_tb;
using namespace axiSocketMaster_tb_ns;
#include "axiSocketExternal.h"

class axiSocketTestbench: public sc_module, public blockBase, public axiSocketChannels {

public:

    std::shared_ptr<axiSocketBase> axiSocket;
    axiSocketExternal external;

    axiSocketTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~axiSocketTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END

#endif /* AXISOCKET_TESTBENCH_H */
