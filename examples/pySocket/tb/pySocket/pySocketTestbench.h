#ifndef PYSOCKET_TANDEM_H
#define PYSOCKET_TANDEM_H
// 

// GENERATED_CODE_PARAM --block=pySocket
// GENERATED_CODE_BEGIN --template=testbench --section=header
#include "systemc.h"
#include "instanceFactory.h"

import pySocket.base;
import pySocket_tb;
using namespace pySocket_tb_ns;
#include "pySocketExternal.h"

class pySocketTestbench: public sc_module, public blockBase, public pySocketChannels {

public:

    std::shared_ptr<pySocketBase> pySocket;
    pySocketExternal external;

    pySocketTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~pySocketTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END

#endif /* PYSOCKET_TANDEM_H */
