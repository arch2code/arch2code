//

// GENERATED_CODE_PARAM --block=xpCstSharedSrc --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpCstShared_xpCstSharedSrc.base;
import xpCstShared_xpCstSharedDefs;
using namespace xpCstShared_xpCstSharedDefs_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpCstSharedSrcBase : public virtual blockPortBase
{
public:
    virtual ~xpCstSharedSrcBase() = default;
    static constexpr auto CSH_WIDTH = Config::CSH_WIDTH;
    // src ports
    // cshIf->uChk: Shared parameterized pixel push/ack stream
    push_ack_out< cshSt<Config> > out;


    xpCstSharedSrcBase(std::string name, const char * variant) :
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
    using cshPixelT = cshPixelT<Config>;
    using cshSt = cshSt<Config>;
};
export template<typename Config>
class xpCstSharedSrcInverted : public virtual blockPortBase
{
public:
    // src ports
    // cshIf->uChk: Shared parameterized pixel push/ack stream
    push_ack_in< cshSt<Config> > out;


    xpCstSharedSrcInverted(std::string name) :
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
export template<typename Config>
class xpCstSharedSrcChannels
{
public:
    // src ports
    // Shared parameterized pixel push/ack stream
    push_ack_channel< cshSt<Config> > out;


    xpCstSharedSrcChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName)
    {};
    void bind( xpCstSharedSrcBase<Config> *a, xpCstSharedSrcInverted<Config> *b)
    {
        a->out( out );
        b->out( out );
    };
};

// GENERATED_CODE_END
