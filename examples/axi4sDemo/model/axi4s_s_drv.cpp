//

// GENERATED_CODE_PARAM --block=axi4s_s_drv
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "axi4s_s_drv.h"
SC_HAS_PROCESS(axi4s_s_drv);

axi4s_s_drv::registerBlock axi4s_s_drv::registerBlock_; //register the block with the factory

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