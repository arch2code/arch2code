#ifndef PRODUCER_H
#define PRODUCER_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=producer
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
import producer.base;
#include "axi4_stream_channel.h"
#include "axi_read_channel.h"
#include "axi_write_channel.h"
import axiDemo;
using namespace axiDemo_ns;

SC_MODULE(producer), public blockBase, public producerBase
{
private:

public:

    producer(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~producer() override = default;

    // GENERATED_CODE_END
    // block implementation members
    void outAXI0Rd(void);
    void outAXI1Rd(void);
    void outAXI0Wr(void);
    void outAXI1Wr(void);
    void outAXI2Wr(void);
    void outAXI3Wr(void);
    void outRespHandlerAXI0Wr(void);
    void outRespHandlerAXI1Wr(void);
    void outRespHandlerAXI2Wr(void);
    void outRespHandlerAXI3Wr(void);
};

#endif //PRODUCER_H

