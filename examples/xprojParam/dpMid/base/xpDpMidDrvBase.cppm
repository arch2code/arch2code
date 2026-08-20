//

// GENERATED_CODE_PARAM --block=xpDpMidDrv --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpDpMid_xpDpMidDrv.base;
import xpDpLeaf;
using namespace xpDpLeaf_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpDpMidDrvBase : public virtual blockPortBase
{
public:
    virtual ~xpDpMidDrvBase() = default;
    static constexpr auto DP_WIDTH = Config::DP_WIDTH;
    // src ports
    // dpIf->uMidStd: The leaf IP's own parameterized pixel push/ack stream
    push_ack_out< dpSt<Config> > out;


    xpDpMidDrvBase(std::string name, const char * variant) :
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
    using dpPixelT = dpPixelT<Config>;
    using dpSt = dpSt<Config>;
};
export template<typename Config>
class xpDpMidDrvInverted : public virtual blockPortBase
{
public:
    // src ports
    // dpIf->uMidStd: The leaf IP's own parameterized pixel push/ack stream
    push_ack_in< dpSt<Config> > out;


    xpDpMidDrvInverted(std::string name) :
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
class xpDpMidDrvChannels
{
public:
    // src ports
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< dpSt<Config> > out;


    xpDpMidDrvChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName)
    {};
    void bind( xpDpMidDrvBase<Config> *a, xpDpMidDrvInverted<Config> *b)
    {
        a->out( out );
        b->out( out );
    };
};

// GENERATED_CODE_END
