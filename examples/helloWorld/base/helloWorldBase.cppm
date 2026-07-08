//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=helloWorld --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "pop_ack_channel.h"
#include "push_ack_channel.h"
#include "rdy_vld_channel.h"
#include "req_ack_channel.h"

export module helloWorld.base;
import helloWorld_tb;
using namespace helloWorld_tb_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class helloWorldBase : public virtual blockPortBase
{
public:
    virtual ~helloWorldBase() = default;


    helloWorldBase(std::string name, const char * variant) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class helloWorldInverted : public virtual blockPortBase
{
public:


    helloWorldInverted(std::string name) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class helloWorldChannels
{
public:


    helloWorldChannels(std::string name, std::string srcName) 
    {};
    void bind( helloWorldBase *a, helloWorldInverted *b)
    {
    };
};

// GENERATED_CODE_END
