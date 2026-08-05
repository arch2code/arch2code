//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=apbDecode --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"

export module simple_ip_apbDecode.base;
import common_shared_types;
using namespace common_shared_types_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class apbDecodeBase : public virtual blockPortBase
{
public:
    virtual ~apbDecodeBase() = default;
    // src ports
    // apbReg->uIp: CPU access to registers via APB
    apb_out< apbAddrSt, apbDataSt > apbReg_uIp;

    // dst ports
    // External->apbReg: CPU access to registers via APB
    apb_in< apbAddrSt, apbDataSt > cpu_main;


    apbDecodeBase(std::string name, const char * variant) :
        apbReg_uIp("apbReg_uIp")
        ,cpu_main("cpu_main")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbReg_uIp->setTimed(nsec, mode);
        cpu_main->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbReg_uIp->setLogging(verbosity);
        cpu_main->setLogging(verbosity);
    };
};
export class apbDecodeInverted : public virtual blockPortBase
{
public:
    // src ports
    // apbReg->uIp: CPU access to registers via APB
    apb_in< apbAddrSt, apbDataSt > apbReg_uIp;

    // dst ports
    // External->apbReg: CPU access to registers via APB
    apb_out< apbAddrSt, apbDataSt > cpu_main;


    apbDecodeInverted(std::string name) :
        apbReg_uIp(("apbReg_uIp"+name).c_str())
        ,cpu_main(("cpu_main"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbReg_uIp->setTimed(nsec, mode);
        cpu_main->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbReg_uIp->setLogging(verbosity);
        cpu_main->setLogging(verbosity);
    };
};
export class apbDecodeChannels
{
public:
    // src ports
    // CPU access to registers via APB
    apb_channel< apbAddrSt, apbDataSt > apbReg_uIp;

    // dst ports
    // CPU access to registers via APB
    apb_channel< apbAddrSt, apbDataSt > cpu_main;


    apbDecodeChannels(std::string name, std::string srcName) :
    apbReg_uIp(("apbReg_uIp"+name).c_str(), srcName)
    ,cpu_main(("cpu_main"+name).c_str(), srcName)
    {};
    void bind( apbDecodeBase *a, apbDecodeInverted *b)
    {
        a->apbReg_uIp( apbReg_uIp );
        b->apbReg_uIp( apbReg_uIp );
        a->cpu_main( cpu_main );
        b->cpu_main( cpu_main );
    };
};

// GENERATED_CODE_END
