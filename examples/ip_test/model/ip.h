#ifndef IP_H
#define IP_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=ip
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "ipBase.h"
#include "addressMap.h"
#include "hwRegister.h"
#include "ipIncludes.h"
#include "ip_topIncludes.h"

SC_MODULE(ip), public blockBase, public ipBase
{
private:
    void regHandler(void);
    addressMap regs;

    struct registerBlock
    {
        registerBlock()
        {
            // Register parameter variants with factory
            instanceFactory::addParam({
                { "ip.variant0.IP_DATA_WIDTH", 8 },
                { "ip.variant0.IP_MEM_DEPTH", 16 },
                { "ip.variant1.IP_DATA_WIDTH", 12 },
                { "ip.variant1.IP_MEM_DEPTH", 8 },
            });
            // lamda function to construct the block
            instanceFactory::registerBlock("ip_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<ip>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:

    //registers
    hwRegister< ipCfgSt, 4 > ipCfg; // IP configuration
    hwRegister< ipDataSt, 4 > ipLastData; // Last data word received on ipDataIf

    ip(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ip() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    void dataHandler(void);
};

#endif //IP_H
