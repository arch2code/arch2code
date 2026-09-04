//

// GENERATED_CODE_PARAM --block=vliTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "blockBase.h"

export module vlInh_vliTop.base;
import vlInh_vliCont;
using namespace vlInh_vliCont_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class vliTopBase : public virtual blockPortBase
{
public:
    virtual ~vliTopBase() = default;


    vliTopBase(std::string name, const char * variant)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class vliTopInverted : public virtual blockPortBase
{
public:


    vliTopInverted(std::string name)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class vliTopChannels
{
public:


    vliTopChannels(std::string name, std::string srcName)
    {};
    void bind( vliTopBase *a, vliTopInverted *b)
    {
    };
};

// GENERATED_CODE_END
