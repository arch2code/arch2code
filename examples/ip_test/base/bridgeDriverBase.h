#ifndef BRIDGEDRIVER_BASE_H
#define BRIDGEDRIVER_BASE_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=bridgeDriver
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "push_ack_channel.h"
import ipBridge;
using namespace ipBridge_ns;

class bridgeDriverBase : public virtual blockPortBase
{
public:
    virtual ~bridgeDriverBase() = default;
    // src ports
    // data8If->uBridge: Non-parameterized 8-bit Q10 bridge data interface
    push_ack_out< data8St > out8;
    // data70If->uBridge: Non-parameterized 70-bit Q10 bridge data interface
    push_ack_out< data70St > out70;


    bridgeDriverBase(std::string name, const char * variant) :
        out8("out8")
        ,out70("out70")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out8->setTimed(nsec, mode);
        out70->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out8->setLogging(verbosity);
        out70->setLogging(verbosity);
    };
};
class bridgeDriverInverted : public virtual blockPortBase
{
public:
    // src ports
    // data8If->uBridge: Non-parameterized 8-bit Q10 bridge data interface
    push_ack_in< data8St > out8;
    // data70If->uBridge: Non-parameterized 70-bit Q10 bridge data interface
    push_ack_in< data70St > out70;


    bridgeDriverInverted(std::string name) :
        out8(("out8"+name).c_str())
        ,out70(("out70"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out8->setTimed(nsec, mode);
        out70->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out8->setLogging(verbosity);
        out70->setLogging(verbosity);
    };
};
class bridgeDriverChannels
{
public:
    // src ports
    // Non-parameterized 8-bit Q10 bridge data interface
    push_ack_channel< data8St > out8;
    // Non-parameterized 70-bit Q10 bridge data interface
    push_ack_channel< data70St > out70;


    bridgeDriverChannels(std::string name, std::string srcName) :
    out8(("out8"+name).c_str(), srcName)
    ,out70(("out70"+name).c_str(), srcName)
    {};
    void bind( bridgeDriverBase *a, bridgeDriverInverted *b)
    {
        a->out8( out8 );
        b->out8( out8 );
        a->out70( out70 );
        b->out70( out70 );
    };
};


// Force-link function (active modules-mode anchor). See plan-block-registration.md.
void force_link_bridgeDriver();
// GENERATED_CODE_END
#endif //BRIDGEDRIVER_BASE_H
