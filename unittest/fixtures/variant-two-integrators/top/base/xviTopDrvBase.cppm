//

// GENERATED_CODE_PARAM --block=xviTopDrv --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xviTop_xviTopDrv.base;
import xviLeaf;
using namespace xviLeaf_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xviTopDrvBase : public virtual blockPortBase
{
public:
    virtual ~xviTopDrvBase() = default;
    static constexpr auto XVI_WIDTH = Config::XVI_WIDTH;
    // src ports
    // xviIf->uTopLeaf: The leaf IP's own parameterized pixel push/ack stream
    push_ack_out< xviSt<Config> > out;


    xviTopDrvBase(std::string name, const char * variant) :
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
class xviTopDrvInverted : public virtual blockPortBase
{
public:
    // src ports
    // xviIf->uTopLeaf: The leaf IP's own parameterized pixel push/ack stream
    push_ack_in< xviSt<Config> > out;


    xviTopDrvInverted(std::string name) :
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
class xviTopDrvChannels
{
public:
    // src ports
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< xviSt<Config> > out;


    xviTopDrvChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName)
    {};
    void bind( xviTopDrvBase<Config> *a, xviTopDrvInverted<Config> *b)
    {
        a->out( out );
        b->out( out );
    };
};

// GENERATED_CODE_END
