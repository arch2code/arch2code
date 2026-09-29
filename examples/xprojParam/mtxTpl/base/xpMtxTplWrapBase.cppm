//

// GENERATED_CODE_PARAM --block=xpMtxTplWrap --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpMtxTpl_xpMtxTplWrap.base;
import xpMtxTpl_xpMtxTplTop;
import xpMtxIp;
using namespace xpMtxTpl_xpMtxTplTop_ns;
using namespace xpMtxIp_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpMtxTplWrapBase : public virtual blockPortBase
{
public:
    virtual ~xpMtxTplWrapBase() = default;
    static constexpr auto MTX_CH_WIDTH = Config::MTX_CH_WIDTH;


    xpMtxTplWrapBase(std::string name, const char * variant)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
    using mtChPixelT = mtChPixelT<Config>;
    using mtChSt = mtChSt<Config>;
};
export template<typename Config>
class xpMtxTplWrapInverted : public virtual blockPortBase
{
public:


    xpMtxTplWrapInverted(std::string name)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export template<typename Config>
class xpMtxTplWrapChannels
{
public:


    xpMtxTplWrapChannels(std::string name, std::string srcName)
    {};
    void bind( xpMtxTplWrapBase<Config> *a, xpMtxTplWrapInverted<Config> *b)
    {
    };
};

// GENERATED_CODE_END
