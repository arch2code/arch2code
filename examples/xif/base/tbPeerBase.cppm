//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=tbPeer --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xif_tbPeer.base;
import xif;
using namespace xif_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class tbPeerBase : public virtual blockPortBase
{
public:
    virtual ~tbPeerBase() = default;
    static constexpr auto DATA_WIDTH = Config::DATA_WIDTH;
    static constexpr auto FRAME_HEIGHT = Config::FRAME_HEIGHT;
    static constexpr auto FRAME_WIDTH = Config::FRAME_WIDTH;
    // src ports
    // dutStreamIf->uTbPeerB: Parameterized DUT stream (also the connection interface A)
    push_ack_out< streamSt<Config> > out;

    // dst ports
    // uTbPeerA->dutStreamIf: Parameterized DUT stream (also the connection interface A)
    push_ack_in< streamSt<Config> > in;


    tbPeerBase(std::string name, const char * variant) :
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
    using streamDataT = streamDataT<Config>;
    using streamSt = streamSt<Config>;
};
export template<typename Config>
class tbPeerInverted : public virtual blockPortBase
{
public:
    // src ports
    // dutStreamIf->uTbPeerB: Parameterized DUT stream (also the connection interface A)
    push_ack_in< streamSt<Config> > out;

    // dst ports
    // uTbPeerA->dutStreamIf: Parameterized DUT stream (also the connection interface A)
    push_ack_out< streamSt<Config> > in;


    tbPeerInverted(std::string name) :
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
class tbPeerChannels
{
public:
    // src ports
    // Parameterized DUT stream (also the connection interface A)
    push_ack_channel< streamSt<Config> > out;

    // dst ports
    // Parameterized DUT stream (also the connection interface A)
    push_ack_channel< streamSt<Config> > in;


    tbPeerChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName)
    ,in(("in"+name).c_str(), srcName)
    {};
    void bind( tbPeerBase<Config> *a, tbPeerInverted<Config> *b)
    {
        a->out( out );
        b->out( out );
        a->in( in );
        b->in( in );
    };
};

// GENERATED_CODE_END
