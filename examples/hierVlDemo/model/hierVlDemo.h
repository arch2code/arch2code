#ifndef AXI4SDEMO_H
#define AXI4SDEMO_H

//

#include "systemc.h"
#include "hierVlDemo_utils.h"

// GENERATED_CODE_PARAM --block=hierVlDemo
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
import hierVlDemo.base;
#include "axi4_stream_channel.h"
import hierVlDemo_tb;
using namespace hierVlDemo_tb_ns;

SC_MODULE(hierVlDemo), public blockBase, public hierVlDemoBase
{
private:

public:

    hierVlDemo(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~hierVlDemo() override = default;

    // GENERATED_CODE_END
    // block implementation members

    void axis4_t1_listener_thread();
    void axis4_t2_driver_thread();

    typedef axi4StreamInfoSt<data_t1_t, tid_t1_t, tdest_t1_t, tuser_t1_t> axis4_t1_info_t;
    typedef axi4StreamInfoSt<data_t2_t, tid_t2_t, tdest_t2_t, tuser_t2_t> axis4_t2_info_t;

    sc_fifo<axis4_t1_info_t> axis4_t1_fifo;

};

#endif //AXI4SDEMO_H
