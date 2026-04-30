//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

// GENERATED_CODE_PARAM --block=ip_top
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "ip_top.h"
#include "apbDecodeBase.h"
#include "srcBase.h"
#include "ipBase.h"
SC_HAS_PROCESS(ip_top);

ip_top::registerBlock ip_top::registerBlock_; //register the block with the factory

ip_top::ip_top(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("ip_top", name(), bbMode)
        ,ip_topBase(name(), variant)
        ,out0("ip_out0", "src")
        ,out1("ip_out1", "src")
        ,apb_uIp0("ip_apb_uIp0", "apbDecode")
        ,apb_uIp1("ip_apb_uIp1", "apbDecode")
        ,uAPBDecode(std::dynamic_pointer_cast<apbDecodeBase>( instanceFactory::createInstance(name(), "uAPBDecode", "apbDecode", "")))
        ,uSrc(std::dynamic_pointer_cast<srcBase>( instanceFactory::createInstance(name(), "uSrc", "src", "")))
        ,uIp0(std::dynamic_pointer_cast<ipBase>( instanceFactory::createInstance(name(), "uIp0", "ip", "variant0")))
        ,uIp1(std::dynamic_pointer_cast<ipBase>( instanceFactory::createInstance(name(), "uIp1", "ip", "variant1")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uAPBDecode->cpu_main(cpu_main);
    // instance to instance connections via channel
    uSrc->out0(out0);
    uIp0->ipDataIf(out0);
    uSrc->out1(out1);
    uIp1->ipDataIf(out1);
    uAPBDecode->apb_uIp0(apb_uIp0);
    uIp0->apbReg(apb_uIp0);
    uAPBDecode->apb_uIp1(apb_uIp1);
    uIp1->apbReg(apb_uIp1);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

