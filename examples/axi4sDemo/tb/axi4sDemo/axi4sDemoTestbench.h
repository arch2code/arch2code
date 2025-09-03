#ifndef AXI4SDEMO_TANDEM_H
#define AXI4SDEMO_TANDEM_H
// 

// GENERATED_CODE_PARAM --block=axi4sDemo
// GENERATED_CODE_BEGIN --template=testbench --section=header
#include "systemc.h"
#include "instanceFactory.h"

#include "axi4sDemoBase.h"
#include "axi4sDemoExternal.h"

class axi4sDemoTestbench: public sc_module, public blockBase, public axi4sDemoChannels {

    private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("axi4sDemoTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<axi4sDemoTestbench>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;

public:

    std::shared_ptr<axi4sDemoBase> axi4sDemo;
    axi4sDemoExternal external;

    axi4sDemoTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~axi4sDemoTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END

#endif /* AXI4SDEMO_TANDEM_H */
