#ifndef AXIDEMO_H
#define AXIDEMO_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=axiDemo
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
import axiDemo.base;
#include "axi4_stream_channel.h"
#include "axi_read_channel.h"
#include "axi_write_channel.h"
import axiDemo;
using namespace axiDemo_ns;
//contained instances base module imports
import producer.base;
import consumer.base;

SC_MODULE(axiDemo), public blockBase, public axiDemoBase
{
private:

public:
    // channels
    // AXI Read channels; Address and Data
    axi_read_channel< axiAddrSt, axiDataSt > axiRd0;
    // AXI Read channels; Address and Data
    axi_read_channel< axiAddrSt, axiDataSt > axiRd1;
    // AXI Read channels; Address and Data
    axi_read_channel< axiAddrSt, axiDataSt > axiRd2;
    // AXI Read channels; Address and Data
    axi_read_channel< axiAddrSt, axiDataSt > axiRd3;
    // AXI Write channels; Address, Data, and Response
    axi_write_channel< axiAddrSt, axiDataSt, axiStrobeSt > axiWr0;
    // AXI Write channels; Address, Data, and Response
    axi_write_channel< axiAddrSt, axiDataSt, axiStrobeSt > axiWr1;
    // AXI Write channels; Address, Data, and Response
    axi_write_channel< axiAddrSt, axiDataSt, axiStrobeSt > axiWr2;
    // AXI Write channels; Address, Data, and Response
    axi_write_channel< axiAddrSt, axiDataSt, axiStrobeSt > axiWr3;
    // AXI stream channel
    axi4_stream_channel< axiDataSt, axiAddrSt, axiAddrSt, axiAddrSt > axiStr0;
    // AXI stream channel
    axi4_stream_channel< axiDataSt, axiAddrSt, axiAddrSt, axiAddrSt > axiStr1;

    //instances contained in block
    std::shared_ptr<producerBase> uProducer;
    std::shared_ptr<consumerBase> uConsumer;

    axiDemo(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~axiDemo() override = default;

    // GENERATED_CODE_END
    // block implementation members

    // Bridges testController completion to the end-of-test voting mechanism.
    void doneTest(void);

};

#endif //AXIDEMO_H
