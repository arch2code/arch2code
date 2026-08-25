//

// GENERATED_CODE_PARAM --block=pySocket_tb --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "axi4_stream_channel.h"
#include "notify_ack_channel.h"
#include "pop_ack_channel.h"
#include "push_ack_channel.h"
#include "rdy_vld_channel.h"
#include "req_ack_channel.h"

export module pySocket_tb.base;
import pySocket_tb;
using namespace pySocket_tb_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class pySocket_tbBase : public virtual blockPortBase
{
public:
    virtual ~pySocket_tbBase() = default;


    pySocket_tbBase(std::string name, const char * variant) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class pySocket_tbInverted : public virtual blockPortBase
{
public:


    pySocket_tbInverted(std::string name) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class pySocket_tbChannels
{
public:


    pySocket_tbChannels(std::string name, std::string srcName) 
    {};
    void bind( pySocket_tbBase *a, pySocket_tbInverted *b)
    {
    };
};

// GENERATED_CODE_END
