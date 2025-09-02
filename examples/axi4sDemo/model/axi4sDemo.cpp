//

// GENERATED_CODE_PARAM --block=axi4sDemo
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "axi4sDemo.h"
SC_HAS_PROCESS(axi4sDemo);

axi4sDemo::registerBlock axi4sDemo::registerBlock_; //register the block with the factory

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
        axis4_t1_fifo.write(info);
        wait(SC_ZERO_TIME); // allow other threads to run
    }
}

void axi4sDemo::axis4_t2_driver_thread()
{
    while (true) {
        axis4_t1_info_t us_info;
        axis4_t2_info_t ds_info;
        us_info = axis4_t1_fifo.read();

        // Split the transaction based on downsize ratio between upstream and downstream
        for(int i=0; i<4; i++) {
            for(int j=0; j<8; j++) {
                ds_info.tdata.data = us_info.tdata.data.word[i];
                ds_info.tstrb[j] = us_info.tstrb[i*8 + j];
                ds_info.tkeep[j] = us_info.tkeep[i*8 + j];
            }
            ds_info.tuser.parity = calc_t2_parity(ds_info.tdata.data);
            ds_info.tid.tid = us_info.tid.tid;
            ds_info.tdest.tid = us_info.tdest.tid;
            ds_info.tlast = (i==3) ? us_info.tlast : false;
            axis4_t2->sendInfo(ds_info);
            wait(SC_ZERO_TIME);
        }

    }
}

bv4_t axi4sDemo::calc_t2_parity(bv64_t data)
{
    bv4_t parity = 0;
    for(int i=0; i<64; i++) {
        parity ^= (data >> i) & 0x7;
    }
    return(parity);
}