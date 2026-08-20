//

// GENERATED_CODE_PARAM --block=xpDpChk --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpDpTop_xpDpChk.base;
import xpDpLeaf;
using namespace xpDpLeaf_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpDpChkBase : public virtual blockPortBase
{
public:
    virtual ~xpDpChkBase() = default;
    static constexpr auto DP_ALGO = Config::DP_ALGO;
    static constexpr auto DP_WIDTH = Config::DP_WIDTH;
    // dst ports
    // uMid->dpIf: The leaf IP's own parameterized pixel push/ack stream
    push_ack_in< dpSt<Config> > in;


    xpDpChkBase(std::string name, const char * variant) :
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
    using dpPixelT = dpPixelT<Config>;
    using dpSt = dpSt<Config>;
};
export template<typename Config>
class xpDpChkInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uMid->dpIf: The leaf IP's own parameterized pixel push/ack stream
    push_ack_out< dpSt<Config> > in;


    xpDpChkInverted(std::string name) :
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
class xpDpChkChannels
{
public:
    // dst ports
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< dpSt<Config> > in;


    xpDpChkChannels(std::string name, std::string srcName) :
    in(("in"+name).c_str(), srcName)
    {};
    void bind( xpDpChkBase<Config> *a, xpDpChkInverted<Config> *b)
    {
        a->in( in );
        b->in( in );
    };
};

// GENERATED_CODE_END
