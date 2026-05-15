//

// GENERATED_CODE_PARAM --block=axi4sDemo
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "axi4sDemo.h"
SC_HAS_PROCESS(axi4sDemo);

// === Block factory registration (axi4sDemo) ===
void force_link_axi4sDemo() {}

void register_axi4sDemo_variants() {
    instanceFactory::registerBlock("axi4sDemo_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<axi4sDemo>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] int _axi4sDemo_registered = (register_axi4sDemo_variants(), 0);
} // namespace
// === End block factory registration ===

axi4sDemo::axi4sDemo(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("axi4sDemo", name(), bbMode)
        ,axi4sDemoBase(name(), variant)
// GENERATED_CODE_END
        ,axis4_t1_fifo("axis4_t1_fifo", 4)
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END

    SC_THREAD(axis4_t1_listener_thread);
    SC_THREAD(axis4_t2_driver_thread);

};

void axi4sDemo::axis4_t1_listener_thread()
{
    while (true) {
        // Push to receive fifo
        axis4_t1_info_t info;
        axis4_t1->receiveInfo(info);
        // Check Parity
        Q_ASSERT(check_parity_t1(info.tdata.data, info.tuser.parity), "Parity mismatch");
        axis4_t1_fifo.write(info);
        wait(SC_ZERO_TIME); // allow other threads to run
    }
}

void axi4sDemo::axis4_t2_driver_thread()
{
    while (true) {
        axis4_t1_info_t t1_info;
        axis4_t2_info_t t2_info;
        t1_info = axis4_t1_fifo.read();

        // Split the transaction based on downsize ratio between upstream and downstream
        for(int i=0; i<4; i++) {
            for(int j=0; j<8; j++) {
                t2_info.tdata.data = t1_info.tdata.data.word[i];
                t2_info.tstrb[j] = t1_info.tstrb[i*8 + j];
                t2_info.tkeep[j] = t1_info.tkeep[i*8 + j];
            }
            t2_info.tuser.parity = calc_parity_t2(t2_info.tdata.data);
            t2_info.tid.tid = t1_info.tid.tid;
            t2_info.tdest.tid = t1_info.tdest.tid;
            t2_info.tlast = (i==3) ? t1_info.tlast : false;
            axis4_t2->sendInfo(t2_info);
            wait(SC_ZERO_TIME);
        }

    }
}