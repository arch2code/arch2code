//

// GENERATED_CODE_PARAM --block=xviLeaf --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xviLeaf.base;
import xviLeaf;
using namespace xviLeaf_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xviLeafBase : public virtual blockPortBase
{
public:
    virtual ~xviLeafBase() = default;
    static constexpr auto XVI_WIDTH = Config::XVI_WIDTH;
    static constexpr auto XVI_GAIN = Config::XVI_GAIN;
    // src ports
    // xviIf->External: The leaf IP's own parameterized pixel push/ack stream
    push_ack_out< xviSt<Config> > out;

    // dst ports
    // External->xviIf: The leaf IP's own parameterized pixel push/ack stream
    push_ack_in< xviSt<Config> > in;


    xviLeafBase(std::string name, const char * variant) :
        out("out")
        ,in("in")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out->setTimed(nsec, mode);
        in->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out->setLogging(verbosity);
        in->setLogging(verbosity);
    };
    using xviPixelT = xviPixelT<Config>;
    using xviSt = xviSt<Config>;
};
export template<typename Config>
class xviLeafInverted : public virtual blockPortBase
{
public:
    // src ports
    // xviIf->External: The leaf IP's own parameterized pixel push/ack stream
    push_ack_in< xviSt<Config> > out;

    // dst ports
    // External->xviIf: The leaf IP's own parameterized pixel push/ack stream
    push_ack_out< xviSt<Config> > in;


    xviLeafInverted(std::string name) :
        out(("out"+name).c_str())
        ,in(("in"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out->setTimed(nsec, mode);
        in->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out->setLogging(verbosity);
        in->setLogging(verbosity);
    };
};
export template<typename Config>
class xviLeafChannels
{
public:
    // src ports
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< xviSt<Config> > out;

    // dst ports
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< xviSt<Config> > in;


    xviLeafChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName)
    ,in(("in"+name).c_str(), srcName)
    {};
    void bind( xviLeafBase<Config> *a, xviLeafInverted<Config> *b)
    {
        a->out( out );
        b->out( out );
        a->in( in );
        b->in( in );
    };
};

// GENERATED_CODE_END
