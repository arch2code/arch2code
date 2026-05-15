#ifndef IPBRIDGE_BASE_H
#define IPBRIDGE_BASE_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=ipBridge
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "apb_channel.h"
#include "push_ack_channel.h"
import ipBridge;
using namespace ipBridge_ns;
import ip_top;
using namespace ip_top_ns;
import ip;
using namespace ip_ns;

class ipBridgeBase : public virtual blockPortBase
{
public:
    virtual ~ipBridgeBase() = default;
    // dst ports
    // uBridgeDriver->data8If: Non-parameterized 8-bit Q10 bridge data interface
    push_ack_in< data8St > data8In;
    // uBridgeDriver->data70If: Non-parameterized 70-bit Q10 bridge data interface
    push_ack_in< data70St > data70In;
    // uAPBDecode->apbReg: CPU access to IP registers via APB
    apb_in< apbAddrSt, apbDataSt > apbReg;


    ipBridgeBase(std::string name, const char * variant) :
        data8In("data8In")
        ,data70In("data70In")
        ,apbReg("apbReg")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        data8In->setTimed(nsec, mode);
        data70In->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        data8In->setLogging(verbosity);
        data70In->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
};
class ipBridgeInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uBridgeDriver->data8If: Non-parameterized 8-bit Q10 bridge data interface
    push_ack_out< data8St > data8In;
    // uBridgeDriver->data70If: Non-parameterized 70-bit Q10 bridge data interface
    push_ack_out< data70St > data70In;
    // uAPBDecode->apbReg: CPU access to IP registers via APB
    apb_out< apbAddrSt, apbDataSt > apbReg;


    ipBridgeInverted(std::string name) :
        data8In(("data8In"+name).c_str())
        ,data70In(("data70In"+name).c_str())
        ,apbReg(("apbReg"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        data8In->setTimed(nsec, mode);
        data70In->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        data8In->setLogging(verbosity);
        data70In->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
};
class ipBridgeChannels
{
public:
    // dst ports
    // Non-parameterized 8-bit Q10 bridge data interface
    push_ack_channel< data8St > data8In;
    // Non-parameterized 70-bit Q10 bridge data interface
    push_ack_channel< data70St > data70In;
    // CPU access to IP registers via APB
    apb_channel< apbAddrSt, apbDataSt > apbReg;


    ipBridgeChannels(std::string name, std::string srcName) :
    data8In(("data8In"+name).c_str(), srcName)
    ,data70In(("data70In"+name).c_str(), srcName)
    ,apbReg(("apbReg"+name).c_str(), srcName)
    {};
    void bind( ipBridgeBase *a, ipBridgeInverted *b)
    {
        a->data8In( data8In );
        b->data8In( data8In );
        a->data70In( data70In );
        b->data70In( data70In );
        a->apbReg( apbReg );
        b->apbReg( apbReg );
    };
};


// Force-link function (active modules-mode anchor).
void force_link_ipBridge();
// GENERATED_CODE_END
#endif //IPBRIDGE_BASE_H
