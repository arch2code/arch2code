//

// GENERATED_CODE_PARAM --block=xviDrv --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xviMid_xviDrv.base;
import xviLeaf;
using namespace xviLeaf_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xviDrvBase : public virtual blockPortBase
{
public:
    virtual ~xviDrvBase() = default;
    static constexpr auto XVI_WIDTH = Config::XVI_WIDTH;
    // src ports
    // xviIf->uMidLeaf: The leaf IP's own parameterized pixel push/ack stream
    push_ack_out< xviSt<Config> > out;


    xviDrvBase(std::string name, const char * variant) :
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
    using xviPixelT = xviPixelT<Config>;
    using xviSt = xviSt<Config>;
};
export template<typename Config>
class xviDrvInverted : public virtual blockPortBase
{
public:
    // src ports
    // xviIf->uMidLeaf: The leaf IP's own parameterized pixel push/ack stream
    push_ack_in< xviSt<Config> > out;


    xviDrvInverted(std::string name) :
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
class xviDrvChannels
{
public:
    // src ports
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< xviSt<Config> > out;


    xviDrvChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName)
    {};
    void bind( xviDrvBase<Config> *a, xviDrvInverted<Config> *b)
    {
        a->out( out );
        b->out( out );
    };
};

// GENERATED_CODE_END
