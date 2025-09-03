#ifndef AXI4SDEMO_H
#define AXI4SDEMO_H

//

#include "systemc.h"
#include "axi4sDemo_utils.h"

// GENERATED_CODE_PARAM --block=axi4sDemo
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "axi4sDemoBase.h"
#include "axi4sDemo_tbIncludes.h"

SC_MODULE(axi4sDemo), public blockBase, public axi4sDemoBase
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("axi4sDemo_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<axi4sDemo>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:

    // channels


    axi4sDemo(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~axi4sDemo() override = default;

    // GENERATED_CODE_END
    // block implementation members

    void axis4_t1_listener_thread();
    void axis4_t2_driver_thread();

    typedef axi4StreamInfoSt<data_t1_t, tid_t1_t, tdest_t1_t, tuser_t1_t> axis4_t1_info_t;
    typedef axi4StreamInfoSt<data_t2_t, tid_t2_t, tdest_t2_t, tuser_t2_t> axis4_t2_info_t;

    sc_fifo<axis4_t1_info_t> axis4_t1_fifo;

};

#endif //AXI4SDEMO_H
