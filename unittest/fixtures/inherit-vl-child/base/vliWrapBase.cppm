//

// GENERATED_CODE_PARAM --block=vliWrap --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module vlInh_vliWrap.base;
import vlInh_vliCont;
using namespace vlInh_vliCont_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class vliWrapBase : public virtual blockPortBase
{
public:
    virtual ~vliWrapBase() = default;


    vliWrapBase(std::string name, const char * variant)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class vliWrapInverted : public virtual blockPortBase
{
public:


    vliWrapInverted(std::string name)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class vliWrapChannels
{
public:


    vliWrapChannels(std::string name, std::string srcName)
    {};
    void bind( vliWrapBase *a, vliWrapInverted *b)
    {
    };
};

// GENERATED_CODE_END
