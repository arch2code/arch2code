//

// GENERATED_CODE_PARAM --block=xpSktChk --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpSktAsm_xpSktChk.base;
import xpSktIp;
using namespace xpSktIp_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpSktChkBase : public virtual blockPortBase
{
public:
    virtual ~xpSktChkBase() = default;
    static constexpr auto SK_PIXEL_WIDTH = Config::SK_PIXEL_WIDTH;
    // dst ports
    // uLeaf->skSampleIf: The IP's parameterized sample push/ack stream
    push_ack_in< skSampleSt<Config> > in;


    xpSktChkBase(std::string name, const char * variant) :
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
    using skPixelT = skPixelT<Config>;
    using skSampleSt = skSampleSt<Config>;
};
export template<typename Config>
class xpSktChkInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uLeaf->skSampleIf: The IP's parameterized sample push/ack stream
    push_ack_out< skSampleSt<Config> > in;


    xpSktChkInverted(std::string name) :
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
class xpSktChkChannels
{
public:
    // dst ports
    // The IP's parameterized sample push/ack stream
    push_ack_channel< skSampleSt<Config> > in;


    xpSktChkChannels(std::string name, std::string srcName) :
    in(("in"+name).c_str(), srcName)
    {};
    void bind( xpSktChkBase<Config> *a, xpSktChkInverted<Config> *b)
    {
        a->in( in );
        b->in( in );
    };
};

// GENERATED_CODE_END
