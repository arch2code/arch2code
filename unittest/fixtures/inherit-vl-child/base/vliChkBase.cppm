//

// GENERATED_CODE_PARAM --block=vliChk --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module vlInh_vliChk.base;
import vlInh_vliCont;
using namespace vlInh_vliCont_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class vliChkBase : public virtual blockPortBase
{
public:
    virtual ~vliChkBase() = default;
    static constexpr auto VLI_ALGO = Config::VLI_ALGO;
    static constexpr auto VLI_WIDTH = Config::VLI_WIDTH;
    // dst ports
    // uContDef->vliIf: Parameterized pixel push/ack stream
    push_ack_in< vliSt<Config> > in;


    vliChkBase(std::string name, const char * variant) :
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
    using vliPixelT = vliPixelT<Config>;
    using vliSt = vliSt<Config>;
};
export template<typename Config>
class vliChkInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uContDef->vliIf: Parameterized pixel push/ack stream
    push_ack_out< vliSt<Config> > in;


    vliChkInverted(std::string name) :
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
class vliChkChannels
{
public:
    // dst ports
    // Parameterized pixel push/ack stream
    push_ack_channel< vliSt<Config> > in;


    vliChkChannels(std::string name, std::string srcName) :
    in(("in"+name).c_str(), srcName)
    {};
    void bind( vliChkBase<Config> *a, vliChkInverted<Config> *b)
    {
        a->in( in );
        b->in( in );
    };
};

// GENERATED_CODE_END
