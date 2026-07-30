//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipStdDriver --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module ip_ipStdDriver.base;
import ip_ipTop;
using namespace ip_ipTop_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class ipStdDriverBase : public virtual blockPortBase
{
public:
    virtual ~ipStdDriverBase() = default;
    // src ports
    // ipStdData8If->uIp: Non-parameterized container boundary interface for uIp.ipDataIf
    push_ack_out< ipStdData8St > out0;


    ipStdDriverBase(std::string name, const char * variant) :
        out0("out0")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out0->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out0->setLogging(verbosity);
    };
};
export class ipStdDriverInverted : public virtual blockPortBase
{
public:
    // src ports
    // ipStdData8If->uIp: Non-parameterized container boundary interface for uIp.ipDataIf
    push_ack_in< ipStdData8St > out0;


    ipStdDriverInverted(std::string name) :
        out0(("out0"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out0->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out0->setLogging(verbosity);
    };
};
export class ipStdDriverChannels
{
public:
    // src ports
    // Non-parameterized container boundary interface for uIp.ipDataIf
    push_ack_channel< ipStdData8St > out0;


    ipStdDriverChannels(std::string name, std::string srcName) :
    out0(("out0"+name).c_str(), srcName)
    {};
    void bind( ipStdDriverBase *a, ipStdDriverInverted *b)
    {
        a->out0( out0 );
        b->out0( out0 );
    };
};

// GENERATED_CODE_END
