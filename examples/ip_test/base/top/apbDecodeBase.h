#ifndef APBDECODE_BASE_H
#define APBDECODE_BASE_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=apbDecode
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "apb_channel.h"
import shared_types;
using namespace shared_types_ns;

class apbDecodeBase : public virtual blockPortBase
{
public:
    virtual ~apbDecodeBase() = default;
    // src ports
    // apbReg->uBridge: CPU access to registers via APB
    apb_out< apbAddrSt, apbDataSt > apbReg_uBridge;
    // apbReg->uIp0: CPU access to registers via APB
    apb_out< apbAddrSt, apbDataSt > apbReg_uIp0;
    // apbReg->uIp1: CPU access to registers via APB
    apb_out< apbAddrSt, apbDataSt > apbReg_uIp1;

    // dst ports
    // External->apbReg: CPU access to registers via APB
    apb_in< apbAddrSt, apbDataSt > cpu_main;


    apbDecodeBase(std::string name, const char * variant) :
        apbReg_uBridge("apbReg_uBridge")
        ,apbReg_uIp0("apbReg_uIp0")
        ,apbReg_uIp1("apbReg_uIp1")
        ,cpu_main("cpu_main")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbReg_uBridge->setTimed(nsec, mode);
        apbReg_uIp0->setTimed(nsec, mode);
        apbReg_uIp1->setTimed(nsec, mode);
        cpu_main->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbReg_uBridge->setLogging(verbosity);
        apbReg_uIp0->setLogging(verbosity);
        apbReg_uIp1->setLogging(verbosity);
        cpu_main->setLogging(verbosity);
    };
};
class apbDecodeInverted : public virtual blockPortBase
{
public:
    // src ports
    // apbReg->uBridge: CPU access to registers via APB
    apb_in< apbAddrSt, apbDataSt > apbReg_uBridge;
    // apbReg->uIp0: CPU access to registers via APB
    apb_in< apbAddrSt, apbDataSt > apbReg_uIp0;
    // apbReg->uIp1: CPU access to registers via APB
    apb_in< apbAddrSt, apbDataSt > apbReg_uIp1;

    // dst ports
    // External->apbReg: CPU access to registers via APB
    apb_out< apbAddrSt, apbDataSt > cpu_main;


    apbDecodeInverted(std::string name) :
        apbReg_uBridge(("apbReg_uBridge"+name).c_str())
        ,apbReg_uIp0(("apbReg_uIp0"+name).c_str())
        ,apbReg_uIp1(("apbReg_uIp1"+name).c_str())
        ,cpu_main(("cpu_main"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbReg_uBridge->setTimed(nsec, mode);
        apbReg_uIp0->setTimed(nsec, mode);
        apbReg_uIp1->setTimed(nsec, mode);
        cpu_main->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbReg_uBridge->setLogging(verbosity);
        apbReg_uIp0->setLogging(verbosity);
        apbReg_uIp1->setLogging(verbosity);
        cpu_main->setLogging(verbosity);
    };
};
class apbDecodeChannels
{
public:
    // src ports
    // CPU access to registers via APB
    apb_channel< apbAddrSt, apbDataSt > apbReg_uBridge;
    // CPU access to registers via APB
    apb_channel< apbAddrSt, apbDataSt > apbReg_uIp0;
    // CPU access to registers via APB
    apb_channel< apbAddrSt, apbDataSt > apbReg_uIp1;

    // dst ports
    // CPU access to registers via APB
    apb_channel< apbAddrSt, apbDataSt > cpu_main;


    apbDecodeChannels(std::string name, std::string srcName) :
    apbReg_uBridge(("apbReg_uBridge"+name).c_str(), srcName)
    ,apbReg_uIp0(("apbReg_uIp0"+name).c_str(), srcName)
    ,apbReg_uIp1(("apbReg_uIp1"+name).c_str(), srcName)
    ,cpu_main(("cpu_main"+name).c_str(), srcName)
    {};
    void bind( apbDecodeBase *a, apbDecodeInverted *b)
    {
        a->apbReg_uBridge( apbReg_uBridge );
        b->apbReg_uBridge( apbReg_uBridge );
        a->apbReg_uIp0( apbReg_uIp0 );
        b->apbReg_uIp0( apbReg_uIp0 );
        a->apbReg_uIp1( apbReg_uIp1 );
        b->apbReg_uIp1( apbReg_uIp1 );
        a->cpu_main( cpu_main );
        b->cpu_main( cpu_main );
    };
};

// GENERATED_CODE_END
#endif //APBDECODE_BASE_H
