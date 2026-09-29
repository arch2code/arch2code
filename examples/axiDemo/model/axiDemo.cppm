//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=axiDemo --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "axi4_stream_channel.h"
#include "axi_read_channel.h"
#include "axi_write_channel.h"
// GENERATED_CODE_END
#include "testController.h"
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module axiDemo.block;
import axiDemo.base;
import axiDemo;
import axiDemo_producer.base;
import axiDemo_consumer.base;
// GENERATED_CODE_END
// user imports here
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace axiDemo_ns;
export SC_MODULE(axiDemo), public blockBase, public axiDemoBase
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

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(axiDemo);

// === Block factory registration (axiDemo) ===
void register_axiDemo_variants() {
    instanceFactory::registerBlock("axiDemo_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<axiDemo>(blockName, variant, bbMode)); }, "", "axiDemo");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _axiDemo_registered = (register_axiDemo_variants(), 0);
} // namespace
// === End block factory registration ===

axiDemo::axiDemo(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("axiDemo", name(), bbMode)
        ,axiDemoBase(name(), variant)
        ,axiRd0("consumer_axiRd0", "producer", "api_list_size", 256, "")
        ,axiRd1("consumer_axiRd1", "producer", "api_list_size", 256, "")
        ,axiRd2("consumer_axiRd2", "producer", "api_list_size", 256, "")
        ,axiRd3("consumer_axiRd3", "producer", "api_list_size", 256, "")
        ,axiWr0("consumer_axiWr0", "producer", "api_list_size", 256, "")
        ,axiWr1("consumer_axiWr1", "producer", "api_list_size", 256, "")
        ,axiWr2("consumer_axiWr2", "producer", "api_list_size", 256, "")
        ,axiWr3("consumer_axiWr3", "producer", "api_list_size", 256, "")
        ,axiStr0("consumer_axiStr0", "producer", "api_list_size", 256, "")
        ,axiStr1("consumer_axiStr1", "producer", "api_list_size", 256, "")
        ,uProducer(std::dynamic_pointer_cast<producerBase>(instanceFactory::createInstance(name(), "uProducer", "producer", "", "axiDemo")))
        ,uConsumer(std::dynamic_pointer_cast<consumerBase>(instanceFactory::createInstance(name(), "uConsumer", "consumer", "", "axiDemo")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    uProducer->axiRd0(axiRd0);
    uConsumer->axiRd0(axiRd0);
    uProducer->axiRd1(axiRd1);
    uConsumer->axiRd1(axiRd1);
    uProducer->axiRd2(axiRd2);
    uConsumer->axiRd2(axiRd2);
    uProducer->axiRd3(axiRd3);
    uConsumer->axiRd3(axiRd3);
    uProducer->axiWr0(axiWr0);
    uConsumer->axiWr0(axiWr0);
    uProducer->axiWr1(axiWr1);
    uConsumer->axiWr1(axiWr1);
    uProducer->axiWr2(axiWr2);
    uConsumer->axiWr2(axiWr2);
    uProducer->axiWr3(axiWr3);
    uConsumer->axiWr3(axiWr3);
    uProducer->axiStr0(axiStr0);
    uConsumer->axiStr0(axiStr0);
    uProducer->axiStr1(axiStr1);
    uConsumer->axiStr1(axiStr1);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(doneTest);
};

// End-of-test bridge: the model is self-driving via testController. Wait for all
// registered tests to complete, then vote end-of-test so axiDemoExternal::eotThread
// can sc_stop() the simulation.
void axiDemo::doneTest(void)
{
    endOfTest eot;
    eot.registerVoter();
    testController::GetInstance().wait_all_tests_complete();
    eot.setEndOfTest(true);
}

