#ifndef SRC_BASE_H
#define SRC_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=src
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "push_ack_channel.h"
#include "ipIncludes.h"

class srcBase : public virtual blockPortBase
{
public:
    virtual ~srcBase() = default;
    // src ports
    // ipDataIf->uIp0: IP data push/ack stream
    push_ack_out< ipDataSt > out0;
    // ipDataIf->uIp1: IP data push/ack stream
    push_ack_out< ipDataSt > out1;


    srcBase(std::string name, const char * variant) :
        out0("out0")
        ,out1("out1")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out0->setTimed(nsec, mode);
        out1->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out0->setLogging(verbosity);
        out1->setLogging(verbosity);
    };
};
class srcInverted : public virtual blockPortBase
{
public:
    // src ports
    // ipDataIf->uIp0: IP data push/ack stream
    push_ack_in< ipDataSt > out0;
    // ipDataIf->uIp1: IP data push/ack stream
    push_ack_in< ipDataSt > out1;


    srcInverted(std::string name) :
        out0(("out0"+name).c_str())
        ,out1(("out1"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out0->setTimed(nsec, mode);
        out1->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out0->setLogging(verbosity);
        out1->setLogging(verbosity);
    };
};
class srcChannels
{
public:
    // src ports
    // IP data push/ack stream
    push_ack_channel< ipDataSt > out0;
    // IP data push/ack stream
    push_ack_channel< ipDataSt > out1;


    srcChannels(std::string name, std::string srcName) :
    out0(("out0"+name).c_str(), srcName)
    ,out1(("out1"+name).c_str(), srcName)
    {};
    void bind( srcBase *a, srcInverted *b)
    {
        a->out0( out0 );
        b->out0( out0 );
        a->out1( out1 );
        b->out1( out1 );
    };
};

// GENERATED_CODE_END
#endif //SRC_BASE_H
