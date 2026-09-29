//

// GENERATED_CODE_PARAM --block=xpInhDrv --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpInhVar_xpInhDrv.base;
import xpInhVar_xpInhCont;
using namespace xpInhVar_xpInhCont_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpInhDrvBase : public virtual blockPortBase
{
public:
    virtual ~xpInhDrvBase() = default;
    static constexpr auto INH_WIDTH = Config::INH_WIDTH;
    // src ports
    // inhIf->uContDef: Parameterized pixel push/ack stream
    push_ack_out< inhSt<Config> > out;
    // inhIf->uContAlt: Parameterized pixel push/ack stream
    push_ack_out< inhSt<Config> > out2;


    xpInhDrvBase(std::string name, const char * variant) :
        out("out")
        ,out2("out2")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out->setTimed(nsec, mode);
        out2->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out->setLogging(verbosity);
        out2->setLogging(verbosity);
    };
    using inhPixelT = inhPixelT<Config>;
    using inhSt = inhSt<Config>;
};
export template<typename Config>
class xpInhDrvInverted : public virtual blockPortBase
{
public:
    // src ports
    // inhIf->uContDef: Parameterized pixel push/ack stream
    push_ack_in< inhSt<Config> > out;
    // inhIf->uContAlt: Parameterized pixel push/ack stream
    push_ack_in< inhSt<Config> > out2;


    xpInhDrvInverted(std::string name) :
        out(("out"+name).c_str())
        ,out2(("out2"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out->setTimed(nsec, mode);
        out2->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out->setLogging(verbosity);
        out2->setLogging(verbosity);
    };
};
export template<typename Config>
class xpInhDrvChannels
{
public:
    // src ports
    // Parameterized pixel push/ack stream
    push_ack_channel< inhSt<Config> > out;
    // Parameterized pixel push/ack stream
    push_ack_channel< inhSt<Config> > out2;


    xpInhDrvChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName)
    ,out2(("out2"+name).c_str(), srcName)
    {};
    void bind( xpInhDrvBase<Config> *a, xpInhDrvInverted<Config> *b)
    {
        a->out( out );
        b->out( out );
        a->out2( out2 );
        b->out2( out2 );
    };
};

// GENERATED_CODE_END
