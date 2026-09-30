//

// GENERATED_CODE_PARAM --block=vliDrv --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module vlInh_vliDrv.base;
import vlInh_vliCont;
using namespace vlInh_vliCont_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class vliDrvBase : public virtual blockPortBase
{
public:
    virtual ~vliDrvBase() = default;
    static constexpr auto VLI_WIDTH = Config::VLI_WIDTH;
    // src ports
    // vliIf->uContDef: Parameterized pixel push/ack stream
    push_ack_out< vliSt<Config> > out;


    vliDrvBase(std::string name, const char * variant) :
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
    using vliPixelT = vliPixelT<Config>;
    using vliSt = vliSt<Config>;
};
export template<typename Config>
class vliDrvInverted : public virtual blockPortBase
{
public:
    // src ports
    // vliIf->uContDef: Parameterized pixel push/ack stream
    push_ack_in< vliSt<Config> > out;


    vliDrvInverted(std::string name) :
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
class vliDrvChannels
{
public:
    // src ports
    // Parameterized pixel push/ack stream
    push_ack_channel< vliSt<Config> > out;


    vliDrvChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName)
    {};
    void bind( vliDrvBase<Config> *a, vliDrvInverted<Config> *b)
    {
        a->out( out );
        b->out( out );
    };
};

// GENERATED_CODE_END
