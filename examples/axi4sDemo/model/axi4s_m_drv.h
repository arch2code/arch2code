#ifndef AXI4S_M_DRV_H
#define AXI4S_M_DRV_H

//

#include "systemc.h"

// GENERATED_CODE_PARAM --block=axi4s_m_drv
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "axi4s_m_drvBase.h"
#include "axi4sDemo_tbIncludes.h"

SC_MODULE(axi4s_m_drv), public blockBase, public axi4s_m_drvBase
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("axi4s_m_drv_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<axi4s_m_drv>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:

    // channels


    axi4s_m_drv(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~axi4s_m_drv() override = default;

    // GENERATED_CODE_END
    // block implementation members

    typedef axi4StreamInfoSt<data_t1_t, tid_t1_t, tdest_t1_t, tuser_t1_t> t1_info_t;

    void axis4_t1_driver_thread();

    bv16_t calc_parity(bv256_t data);

    typedef t1_info_t t1_frame_t [1024];

    t1_frame_t frame;


};

#endif //AXI4S_M_DRV_H
