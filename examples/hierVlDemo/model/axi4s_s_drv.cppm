//

// GENERATED_CODE_PARAM --block=axi4s_s_drv --mode=module
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
#include "endOfTest.h"
#include "hierVlDemo_utils.h"
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module hierVlDemo_axi4s_s_drv.block;
import hierVlDemo_axi4s_s_drv.base;
import hierVlDemo_tb;
using namespace hierVlDemo_tb_ns;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
export SC_MODULE(axi4s_s_drv), public blockBase, public axi4s_s_drvBase
{
private:

public:

    axi4s_s_drv(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~axi4s_s_drv() override = default;

    // GENERATED_CODE_END
    // block implementation members

    typedef axi4StreamInfoSt<data_t2_t, tid_t2_t, tdest_t2_t, tuser_t2_t> t2_info_t;

    void axis4_t2_driver_thread();

    private:
    endOfTest m_eot;
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(axi4s_s_drv);

// === Block factory registration (axi4s_s_drv) ===
void register_axi4s_s_drv_variants() {
    instanceFactory::registerBlock("axi4s_s_drv_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<axi4s_s_drv>(blockName, variant, bbMode)); }, "", "hierVlDemo");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _axi4s_s_drv_registered = (register_axi4s_s_drv_variants(), 0);
} // namespace
// === End block factory registration ===

axi4s_s_drv::axi4s_s_drv(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("axi4s_s_drv", name(), bbMode)
        ,axi4s_s_drvBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(axis4_t2_driver_thread);
};

void axi4s_s_drv::axis4_t2_driver_thread()
{
    int unsigned num_frames = 0;
    int unsigned num_data = 0;
    m_eot.registerVoter();
    while (true) {
        // Pop from send fifo
        t2_info_t info;
        axis4_t2->receiveInfo(info);
        Q_ASSERT(check_parity_t2(info.tdata.data, info.tuser.parity), "Parity mismatch");
        num_data++;
        if(info.tlast) {
            num_frames++;
            log_.logPrint(std::format("Frame {} received", num_frames), LOG_ALWAYS);
            Q_ASSERT(num_data==4096, std::format("Frame length mismatch expected ({})", num_data));
            num_data = 0;
        }
        wait(SC_ZERO_TIME); // allow other threads to run
        if(num_frames==4) break;
    }
    m_eot.setEndOfTest(true);
}

