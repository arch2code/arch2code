//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=xpRtPrimeDecode --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"

export module xpRtInh_xpRtPrimeDecode.base;
import common_shared_types;
using namespace common_shared_types_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xpRtPrimeDecodeBase : public virtual blockPortBase
{
public:
    virtual ~xpRtPrimeDecodeBase() = default;
    // src ports
    // apbReg->uWrap: CPU access to registers via APB
    apb_out< apbAddrSt, apbDataSt > apbReg_uWrap;

    // dst ports
    // External->apbReg: CPU access to registers via APB
    apb_in< apbAddrSt, apbDataSt > cpu_main;


    xpRtPrimeDecodeBase(std::string name, const char * variant) :
        apbReg_uWrap("apbReg_uWrap")
        ,cpu_main("cpu_main")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbReg_uWrap->setTimed(nsec, mode);
        cpu_main->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbReg_uWrap->setLogging(verbosity);
        cpu_main->setLogging(verbosity);
    };
};
export class xpRtPrimeDecodeInverted : public virtual blockPortBase
{
public:
    // src ports
    // apbReg->uWrap: CPU access to registers via APB
    apb_in< apbAddrSt, apbDataSt > apbReg_uWrap;

    // dst ports
    // External->apbReg: CPU access to registers via APB
    apb_out< apbAddrSt, apbDataSt > cpu_main;


    xpRtPrimeDecodeInverted(std::string name) :
        apbReg_uWrap(("apbReg_uWrap"+name).c_str())
        ,cpu_main(("cpu_main"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbReg_uWrap->setTimed(nsec, mode);
        cpu_main->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbReg_uWrap->setLogging(verbosity);
        cpu_main->setLogging(verbosity);
    };
};
export class xpRtPrimeDecodeChannels
{
public:
    // src ports
    // CPU access to registers via APB
    apb_channel< apbAddrSt, apbDataSt > apbReg_uWrap;

    // dst ports
    // CPU access to registers via APB
    apb_channel< apbAddrSt, apbDataSt > cpu_main;


    xpRtPrimeDecodeChannels(std::string name, std::string srcName) :
    apbReg_uWrap(("apbReg_uWrap"+name).c_str(), srcName)
    ,cpu_main(("cpu_main"+name).c_str(), srcName)
    {};
    void bind( xpRtPrimeDecodeBase *a, xpRtPrimeDecodeInverted *b)
    {
        a->apbReg_uWrap( apbReg_uWrap );
        b->apbReg_uWrap( apbReg_uWrap );
        a->cpu_main( cpu_main );
        b->cpu_main( cpu_main );
    };
};

// GENERATED_CODE_END
