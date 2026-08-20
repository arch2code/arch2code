//

// GENERATED_CODE_PARAM --block=xpInhChk --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpInhVar_xpInhChk.base;
import xpInhVar_xpInhCont;
using namespace xpInhVar_xpInhCont_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpInhChkBase : public virtual blockPortBase
{
public:
    virtual ~xpInhChkBase() = default;
    static constexpr auto INH_ALGO = Config::INH_ALGO;
    static constexpr auto INH_WIDTH = Config::INH_WIDTH;
    // dst ports
    // uContDef->inhIf: Parameterized pixel push/ack stream
    push_ack_in< inhSt<Config> > in;


    xpInhChkBase(std::string name, const char * variant) :
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
    using inhPixelT = inhPixelT<Config>;
    using inhSt = inhSt<Config>;
};
export template<typename Config>
class xpInhChkInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uContDef->inhIf: Parameterized pixel push/ack stream
    push_ack_out< inhSt<Config> > in;


    xpInhChkInverted(std::string name) :
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
class xpInhChkChannels
{
public:
    // dst ports
    // Parameterized pixel push/ack stream
    push_ack_channel< inhSt<Config> > in;


    xpInhChkChannels(std::string name, std::string srcName) :
    in(("in"+name).c_str(), srcName)
    {};
    void bind( xpInhChkBase<Config> *a, xpInhChkInverted<Config> *b)
    {
        a->in( in );
        b->in( in );
    };
};

// GENERATED_CODE_END
