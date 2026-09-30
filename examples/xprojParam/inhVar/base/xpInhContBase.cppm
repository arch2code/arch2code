//

// GENERATED_CODE_PARAM --block=xpInhCont --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpInhVar_xpInhCont.base;
import xpInhVar_xpInhCont;
using namespace xpInhVar_xpInhCont_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpInhContBase : public virtual blockPortBase
{
public:
    virtual ~xpInhContBase() = default;
    static constexpr auto INH_ALGO = Config::INH_ALGO;
    static constexpr auto INH_WIDTH = Config::INH_WIDTH;
    // src ports
    // inhIf->uChkDef: Parameterized pixel push/ack stream
    push_ack_out< inhSt<Config> > contOut;

    // dst ports
    // uDrv->inhIf: Parameterized pixel push/ack stream
    push_ack_in< inhSt<Config> > contIn;


    xpInhContBase(std::string name, const char * variant) :
        contOut("contOut")
        ,contIn("contIn")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        contOut->setTimed(nsec, mode);
        contIn->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        contOut->setLogging(verbosity);
        contIn->setLogging(verbosity);
    };
    using inhPixelT = inhPixelT<Config>;
    using inhSt = inhSt<Config>;
};
export template<typename Config>
class xpInhContInverted : public virtual blockPortBase
{
public:
    // src ports
    // inhIf->uChkDef: Parameterized pixel push/ack stream
    push_ack_in< inhSt<Config> > contOut;

    // dst ports
    // uDrv->inhIf: Parameterized pixel push/ack stream
    push_ack_out< inhSt<Config> > contIn;


    xpInhContInverted(std::string name) :
        contOut(("contOut"+name).c_str())
        ,contIn(("contIn"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        contOut->setTimed(nsec, mode);
        contIn->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        contOut->setLogging(verbosity);
        contIn->setLogging(verbosity);
    };
};
export template<typename Config>
class xpInhContChannels
{
public:
    // src ports
    // Parameterized pixel push/ack stream
    push_ack_channel< inhSt<Config> > contOut;

    // dst ports
    // Parameterized pixel push/ack stream
    push_ack_channel< inhSt<Config> > contIn;


    xpInhContChannels(std::string name, std::string srcName) :
    contOut(("contOut"+name).c_str(), srcName)
    ,contIn(("contIn"+name).c_str(), srcName)
    {};
    void bind( xpInhContBase<Config> *a, xpInhContInverted<Config> *b)
    {
        a->contOut( contOut );
        b->contOut( contOut );
        a->contIn( contIn );
        b->contIn( contIn );
    };
};

// GENERATED_CODE_END
