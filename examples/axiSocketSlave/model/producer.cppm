//

// GENERATED_CODE_PARAM --block=producer --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>
#include "instanceFactory.h"
#include "axi_read_channel.h"
#include "axi_write_channel.h"
// GENERATED_CODE_END
#include "testController.h"
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module axiSocketSlave_producer.block;
import axiSocketSlave_producer.base;
import axiSocketSlave_tb;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace axiSocketSlave_tb_ns;
export SC_MODULE(producer), public blockBase, public producerBase
{
private:

public:

    producer(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~producer() override = default;

    // GENERATED_CODE_END
    void outAXI0Rd(void);
    void outAXI0Wr(void);
    void outRespHandlerAXI0Wr(void);

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(producer);

// === Block factory registration (producer) ===
void register_producer_variants() {
    instanceFactory::registerBlock("producer_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<producer>(blockName, variant, bbMode)); }, "", "axiSocketSlave");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _producer_registered = (register_producer_variants(), 0);
} // namespace
// === End block factory registration ===

producer::producer(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("producer", name(), bbMode)
        ,producerBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(outAXI0Rd);
    SC_THREAD(outAXI0Wr);
    SC_THREAD(outRespHandlerAXI0Wr);
};

#define LOOPCOUNT 4
#define BURST_LEN 3

void producer::outAXI0Rd(void)
{
    axiRd0->setCycleTransaction(PORTTYPE_OUT);
    std::string test_name = "test_axird0";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    for (int loop = 0; loop < LOOPCOUNT; loop++) {
        axiReadAddressSt<axiAddrSt> addr{};
        addr.araddr.addr = loop;
        addr.arsize = 0x2;
        addr.arlen = BURST_LEN;
        addr.arburst = AXIBURST_INCR;
        addr.arid = 0x1;
        axiRd0->sendAddr(addr);
        for (int i = 0; i <= BURST_LEN; i++) {
            axiReadRespSt<axiDataSt> cycleData{};
            axiRd0->receiveDataCycle(cycleData);
            if (cycleData.rresp != AXIRESP_OKAY ||
                cycleData.rid != addr.arid ||
                cycleData.rdata.data != static_cast<axiDataT>(i) * 0x01010101) {
                Q_ASSERT(false, "Read data mismatch");
            }
            if ((i == BURST_LEN && cycleData.rlast == 0) || (i < BURST_LEN && cycleData.rlast == 1)) {
                Q_ASSERT(false, "RLAST mismatch");
            }
        }
    }
    controller.test_complete(test_name);
}

void producer::outAXI0Wr(void)
{
    axiWr0->setCycleTransaction(PORTTYPE_OUT);
    std::string test_name = "test_axiwr0";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    for (int loop = 0; loop < LOOPCOUNT; loop++) {
        axiWriteAddressSt<axiAddrSt> addr{};
        addr.awid = 0x1;
        addr.awaddr.addr = loop;
        addr.awlen = BURST_LEN;
        addr.awsize = 0x2;
        addr.awburst = AXIBURST_INCR;
        axiWr0->sendAddr(addr);
        for (int i = 0; i <= BURST_LEN; i++) {
            axiWriteDataSt<axiDataSt, axiStrobeSt> data{};
            data.wid = addr.awid;
            data.wdata.data = static_cast<axiDataT>(i) * 0x01010101;
            data.wstrb.strobe = 0xF;
            data.wlast = (i == BURST_LEN);
            axiWr0->sendDataCycle(data);
        }
    }
    controller.test_complete(test_name);
}

void producer::outRespHandlerAXI0Wr(void)
{
    std::string test_name = "test_axiwr0";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    for (int loop = 0; loop < LOOPCOUNT; loop++) {
        axiWriteRespSt<> resp{};
        axiWr0->receiveResp(resp);
        if (resp.bresp != AXIRESP_OKAY || resp.bid != 0x1) {
            Q_ASSERT(false, "Write response mismatch");
        }
    }
    controller.test_complete(test_name);
}

