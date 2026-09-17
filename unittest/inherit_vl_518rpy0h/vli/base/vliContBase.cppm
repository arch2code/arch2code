//

// GENERATED_CODE_PARAM --block=vliCont --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module vlInh_vliCont.base;
import vlInh_vliCont;
using namespace vlInh_vliCont_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class vliContBase : public virtual blockPortBase
{
public:
    virtual ~vliContBase() = default;
    static constexpr auto VLI_ALGO = Config::VLI_ALGO;
    static constexpr auto VLI_WIDTH = Config::VLI_WIDTH;
    // src ports
    // vliIf->uChkDef: Parameterized pixel push/ack stream
    push_ack_out< vliSt<Config> > contOut;

    // dst ports
    // uDrvDef->vliIf: Parameterized pixel push/ack stream
    push_ack_in< vliSt<Config> > contIn;


    vliContBase(std::string name, const char * variant) :
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
    using vliPixelT = vliPixelT<Config>;
    using vliSt = vliSt<Config>;
};
export template<typename Config>
class vliContInverted : public virtual blockPortBase
{
public:
    // src ports
    // vliIf->uChkDef: Parameterized pixel push/ack stream
    push_ack_in< vliSt<Config> > contOut;

    // dst ports
    // uDrvDef->vliIf: Parameterized pixel push/ack stream
    push_ack_out< vliSt<Config> > contIn;


    vliContInverted(std::string name) :
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
class vliContChannels
{
public:
    // src ports
    // Parameterized pixel push/ack stream
    push_ack_channel< vliSt<Config> > contOut;

    // dst ports
    // Parameterized pixel push/ack stream
    push_ack_channel< vliSt<Config> > contIn;


    vliContChannels(std::string name, std::string srcName) :
    contOut(("contOut"+name).c_str(), srcName)
    ,contIn(("contIn"+name).c_str(), srcName)
    {};
    void bind( vliContBase<Config> *a, vliContInverted<Config> *b)
    {
        a->contOut( contOut );
        b->contOut( contOut );
        a->contIn( contIn );
        b->contIn( contIn );
    };
};

// GENERATED_CODE_END
