//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipStdTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"
#include "push_ack_channel.h"

export module ipStdTop.base;
import ip;
import ipTop;
using namespace ip_ns;
using namespace ipTop_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class ipStdTopBase : public virtual blockPortBase
{
public:
    virtual ~ipStdTopBase() = default;


    ipStdTopBase(std::string name, const char * variant) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class ipStdTopInverted : public virtual blockPortBase
{
public:


    ipStdTopInverted(std::string name) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class ipStdTopChannels
{
public:


    ipStdTopChannels(std::string name, std::string srcName) 
    {};
    void bind( ipStdTopBase *a, ipStdTopInverted *b)
    {
    };
};

// GENERATED_CODE_END
