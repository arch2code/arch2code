//

// GENERATED_CODE_PARAM --block=axi4s_m_drv --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>
#include "instanceFactory.h"
#include "axi4_stream_channel.h"
// GENERATED_CODE_END
#include "axi4sDemo_utils.h"
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module axi4sDemo_axi4s_m_drv.block;
import axi4sDemo_axi4s_m_drv.base;
import axi4sDemo_tb;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace axi4sDemo_tb_ns;
export SC_MODULE(axi4s_m_drv), public blockBase, public axi4s_m_drvBase
{
private:

public:

    axi4s_m_drv(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~axi4s_m_drv() override = default;

    // GENERATED_CODE_END
    // block implementation members

    typedef axi4StreamInfoSt<data_t1_t, tid_t1_t, tdest_t1_t, tuser_t1_t> t1_info_t;

    void axis4_t1_driver_thread();

    typedef t1_info_t t1_frame_t [1024];

    t1_frame_t frame;
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(axi4s_m_drv);

// === Block factory registration (axi4s_m_drv) ===
void register_axi4s_m_drv_variants() {
    instanceFactory::registerBlock("axi4s_m_drv_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<axi4s_m_drv>(blockName, variant, bbMode)); }, "", "axi4sDemo");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _axi4s_m_drv_registered = (register_axi4s_m_drv_variants(), 0);
} // namespace
// === End block factory registration ===

axi4s_m_drv::axi4s_m_drv(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("axi4s_m_drv", name(), bbMode)
        ,axi4s_m_drvBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(axis4_t1_driver_thread);
};

void axi4s_m_drv::axis4_t1_driver_thread()
{
    wait(10, SC_NS); // FIXME Force wait for 10 ns before starting
    while (true) {
        for (int i = 0; i < 1024; i++) {
            // cast frame[i].tdata.data to uint8_t*
            uint8_t* data8b = reinterpret_cast<uint8_t*>(&frame[i].tdata.data);
            for(int n=0; n<32; n++) {
                data8b[n] = (n + i) & 0xff;
                frame[i].tstrb[n] = (i+n)%17 != 0 ? Q_TRUE : Q_FALSE;
                frame[i].tkeep[n] = (i+n)%21 != 0 ? Q_TRUE : Q_FALSE;
            }
            frame[i].tdest.tid = 0x3;
            frame[i].tid.tid = 0x4;
            frame[i].tuser.parity = calc_parity_t1(frame[i].tdata.data);
            frame[i].tlast = (i==1023) ? true : false;
            axis4_t1->sendInfo(frame[i]);
            wait(SC_ZERO_TIME); // allow other threads to run
        }
    }
}

