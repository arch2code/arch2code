//

// GENERATED_CODE_PARAM --block=xviTopSnk --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xviTop_xviTopSnk.base;
import xviLeaf;
using namespace xviLeaf_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xviTopSnkBase : public virtual blockPortBase
{
public:
    virtual ~xviTopSnkBase() = default;
    static constexpr auto XVI_WIDTH = Config::XVI_WIDTH;
    // dst ports
    // uTopLeaf->xviIf: The leaf IP's own parameterized pixel push/ack stream
    push_ack_in< xviSt<Config> > in;


    xviTopSnkBase(std::string name, const char * variant) :
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
    using xviPixelT = xviPixelT<Config>;
    using xviSt = xviSt<Config>;
};
export template<typename Config>
class xviTopSnkInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uTopLeaf->xviIf: The leaf IP's own parameterized pixel push/ack stream
    push_ack_out< xviSt<Config> > in;


    xviTopSnkInverted(std::string name) :
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
class xviTopSnkChannels
{
public:
    // dst ports
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< xviSt<Config> > in;


    xviTopSnkChannels(std::string name, std::string srcName) :
    in(("in"+name).c_str(), srcName)
    {};
    void bind( xviTopSnkBase<Config> *a, xviTopSnkInverted<Config> *b)
    {
        a->in( in );
        b->in( in );
    };
};

// GENERATED_CODE_END
