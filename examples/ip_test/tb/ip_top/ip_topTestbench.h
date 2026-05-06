#ifndef IP_TOP_TANDEM_H
#define IP_TOP_TANDEM_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip_top
// GENERATED_CODE_BEGIN --template=testbench --section=header
#include "systemc.h"
#include "instanceFactory.h"

#include "ip_topBase.h"
#include "ip_topExternal.h"

class ip_topTestbench: public sc_module, public blockBase, public ip_topChannels<ipDefaultConfig> {

    private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("ip_topTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<ip_topTestbench>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;

public:

    std::shared_ptr<ip_topBase<ipDefaultConfig>> ip_top;
    ip_topExternal external;

    ip_topTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ip_topTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END

#endif /* IP_TOP_TANDEM_H */
