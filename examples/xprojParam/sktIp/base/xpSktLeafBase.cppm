//

// GENERATED_CODE_PARAM --block=xpSktLeaf --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpSktIp_xpSktLeaf.base;
import xpSktIp;
using namespace xpSktIp_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpSktLeafBase : public virtual blockPortBase
{
public:
    virtual ~xpSktLeafBase() = default;
    static constexpr auto SK_PIXEL_WIDTH = Config::SK_PIXEL_WIDTH;
    // src ports
    // skSampleIf->External: The IP's parameterized sample push/ack stream
    push_ack_out< skSampleSt<Config> > out;


    xpSktLeafBase(std::string name, const char * variant) :
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
    using skPixelT = skPixelT<Config>;
    using skSampleSt = skSampleSt<Config>;
};
export template<typename Config>
class xpSktLeafInverted : public virtual blockPortBase
{
public:
    // src ports
    // skSampleIf->External: The IP's parameterized sample push/ack stream
    push_ack_in< skSampleSt<Config> > out;


    xpSktLeafInverted(std::string name) :
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
class xpSktLeafChannels
{
public:
    // src ports
    // The IP's parameterized sample push/ack stream
    push_ack_channel< skSampleSt<Config> > out;


    xpSktLeafChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName)
    {};
    void bind( xpSktLeafBase<Config> *a, xpSktLeafInverted<Config> *b)
    {
        a->out( out );
        b->out( out );
    };
};

// GENERATED_CODE_END
