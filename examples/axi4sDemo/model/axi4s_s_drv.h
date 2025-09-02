#ifndef AXI4S_S_DRV_H
#define AXI4S_S_DRV_H

//

#include "systemc.h"
#include "endOfTest.h"

// GENERATED_CODE_PARAM --block=axi4s_s_drv
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "axi4s_s_drvBase.h"
#include "axi4sDemo_tbIncludes.h"

SC_MODULE(axi4s_s_drv), public blockBase, public axi4s_s_drvBase
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("axi4s_s_drv_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<axi4s_s_drv>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:

    // channels


    axi4s_s_drv(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~axi4s_s_drv() override = default;

    // GENERATED_CODE_END
    // block implementation members

    typedef axi4StreamInfoSt<data_t2_t, tid_t2_t, tdest_t2_t, tuser_t2_t> t2_info_t;

    void axis4_t2_driver_thread();

    private:
    endOfTest m_eot;

};

#endif //AXI4S_S_DRV_H
