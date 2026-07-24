//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=dataGen --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module dataGen.base;
import simple_ip;
using namespace simple_ip_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class dataGenBase : public virtual blockPortBase
{
public:
    virtual ~dataGenBase() = default;
    // src ports
    // simpleDataIf->uIp: Non-parameterized producer -> uIp.ipDataIf boundary
    push_ack_out< simpleData8St > out;


    dataGenBase(std::string name, const char * variant) :
        out("out")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out->setLogging(verbosity);
    };
};
export class dataGenInverted : public virtual blockPortBase
{
public:
    // src ports
    // simpleDataIf->uIp: Non-parameterized producer -> uIp.ipDataIf boundary
    push_ack_in< simpleData8St > out;


    dataGenInverted(std::string name) :
        out(("out"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out->setLogging(verbosity);
    };
};
export class dataGenChannels
{
public:
    // src ports
    // Non-parameterized producer -> uIp.ipDataIf boundary
    push_ack_channel< simpleData8St > out;


    dataGenChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName)
    {};
    void bind( dataGenBase *a, dataGenInverted *b)
    {
        a->out( out );
        b->out( out );
    };
};

// GENERATED_CODE_END
