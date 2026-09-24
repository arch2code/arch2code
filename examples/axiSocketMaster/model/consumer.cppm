//

// GENERATED_CODE_PARAM --block=consumer --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "axi_read_channel.h"
#include "axi_write_channel.h"
// GENERATED_CODE_END
// user #includes here
#include <map>
// GENERATED_CODE_BEGIN --template=moduleExport
export module axiSocketMaster_consumer.block;
import axiSocketMaster_consumer.base;
import axiSocketMaster_tb;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace axiSocketMaster_tb_ns;
export SC_MODULE(consumer), public blockBase, public consumerBase
{
private:

public:

    consumer(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~consumer() override = default;

    // GENERATED_CODE_END
    void inAXI0Rd(void);
    void inAXI0Wr(void);

private:
    // Word-addressed backing store: a write burst stores each beat and a read
    // burst returns what was stored (zero where nothing was written).
    static constexpr axiAddrT BEAT_BYTES = axiDataSt::_byteWidth;
    std::map<axiAddrT, axiDataT> m_memory;

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(consumer);

// === Block factory registration (consumer) ===
void register_consumer_variants() {
    instanceFactory::registerBlock("consumer_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<consumer>(blockName, variant, bbMode)); }, "", "axiSocketMaster");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _consumer_registered = (register_consumer_variants(), 0);
} // namespace
// === End block factory registration ===

consumer::consumer(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("consumer", name(), bbMode)
        ,consumerBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(inAXI0Rd);
    SC_THREAD(inAXI0Wr);
};

void consumer::inAXI0Rd(void)
{
    axiRd0->setCycleTransaction(PORTTYPE_IN);
    while (true) {
        axiReadAddressSt<axiAddrSt> addr{};
        axiRd0->receiveAddr(addr);
        const int num_beats = static_cast<int>(addr.arlen) + 1;
        for (int i = 0; i < num_beats; ++i) {
            axiReadRespSt<axiDataSt> resp{};
            resp.rresp = AXIRESP_OKAY;
            resp.rid = addr.arid;
            const auto word = m_memory.find(static_cast<axiAddrT>(addr.araddr.addr) + i * BEAT_BYTES);
            resp.rdata.data = word == m_memory.end() ? 0 : word->second;
            resp.rlast = (i == num_beats - 1);
            axiRd0->sendDataCycle(resp);
        }
    }
}

void consumer::inAXI0Wr(void)
{
    axiWr0->setCycleTransaction(PORTTYPE_IN);
    while (true) {
        axiWriteAddressSt<axiAddrSt> addr{};
        axiWr0->receiveAddr(addr);
        const int num_beats = static_cast<int>(addr.awlen) + 1;
        axiWriteRespSt<> resp{};
        resp.bresp = AXIRESP_OKAY;
        resp.bid = addr.awid;
        for (int i = 0; i < num_beats; ++i) {
            axiWriteDataSt<axiDataSt, axiStrobeSt> data{};
            axiWr0->receiveDataCycle(data);
            if (data.wid != addr.awid ||
                data.wstrb.strobe != 0xF ||
                ((i == num_beats - 1) != data.wlast)) {
                resp.bresp = AXIRESP_SLVERR;
            }
            m_memory[static_cast<axiAddrT>(addr.awaddr.addr) + i * BEAT_BYTES] = data.wdata.data;
        }
        axiWr0->sendRespCycle(resp);
    }
}
