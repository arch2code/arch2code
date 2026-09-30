//

// GENERATED_CODE_PARAM --block=xpMtxTplTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "blockBase.h"

export module xpMtxTpl_xpMtxTplTop.base;
import xpMtxTpl_xpMtxTplTop;
using namespace xpMtxTpl_xpMtxTplTop_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xpMtxTplTopBase : public virtual blockPortBase
{
public:
    virtual ~xpMtxTplTopBase() = default;


    xpMtxTplTopBase(std::string name, const char * variant)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpMtxTplTopInverted : public virtual blockPortBase
{
public:


    xpMtxTplTopInverted(std::string name)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpMtxTplTopChannels
{
public:


    xpMtxTplTopChannels(std::string name, std::string srcName)
    {};
    void bind( xpMtxTplTopBase *a, xpMtxTplTopInverted *b)
    {
    };
};

// GENERATED_CODE_END
