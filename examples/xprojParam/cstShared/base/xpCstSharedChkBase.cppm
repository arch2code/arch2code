//

// GENERATED_CODE_PARAM --block=xpCstSharedChk --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpCstShared_xpCstSharedChk.base;
import xpCstShared_xpCstSharedDefs;
using namespace xpCstShared_xpCstSharedDefs_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpCstSharedChkBase : public virtual blockPortBase
{
public:
    virtual ~xpCstSharedChkBase() = default;
    static constexpr auto CSH_WIDTH = Config::CSH_WIDTH;
    // dst ports
    // uSrc->cshIf: Shared parameterized pixel push/ack stream
    push_ack_in< cshSt<Config> > in;


    xpCstSharedChkBase(std::string name, const char * variant) :
        in("in")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        in->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        in->setLogging(verbosity);
    };
    using cshPixelT = cshPixelT<Config>;
    using cshSt = cshSt<Config>;
};
export template<typename Config>
class xpCstSharedChkInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uSrc->cshIf: Shared parameterized pixel push/ack stream
    push_ack_out< cshSt<Config> > in;


    xpCstSharedChkInverted(std::string name) :
        in(("in"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        in->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        in->setLogging(verbosity);
    };
};
export template<typename Config>
class xpCstSharedChkChannels
{
public:
    // dst ports
    // Shared parameterized pixel push/ack stream
    push_ack_channel< cshSt<Config> > in;


    xpCstSharedChkChannels(std::string name, std::string srcName) :
    in(("in"+name).c_str(), srcName)
    {};
    void bind( xpCstSharedChkBase<Config> *a, xpCstSharedChkInverted<Config> *b)
    {
        a->in( in );
        b->in( in );
    };
};

// GENERATED_CODE_END
