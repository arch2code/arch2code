#ifndef DUT_H
#define DUT_H

//

#include "systemc.h"

// GENERATED_CODE_PARAM --block=dut
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
import dut.base;
#include "req_ack_channel.h"
import pySocket_tb;
using namespace pySocket_tb_ns;

SC_MODULE(dut), public blockBase, public dutBase
{
private:

public:

    dut(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~dut() override = default;

    // GENERATED_CODE_END
    // block implementation members
    void dutListener(void);
    void dut2PythonListener(void);
};

#endif //DUT_H
