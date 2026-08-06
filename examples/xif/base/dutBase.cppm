//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=dut --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xif_dut.base;
import xif;
using namespace xif_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class dutBase : public virtual blockPortBase
{
public:
    virtual ~dutBase() = default;
    static constexpr auto DATA_WIDTH = Config::DATA_WIDTH;
    // src ports
    // dutStreamIf->uSink: Parameterized DUT stream (also the connection interface A)
    push_ack_out< streamSt<Config> > streamOut;

    // dst ports
    // uSrc->dutStreamIf: Parameterized DUT stream (also the connection interface A)
    push_ack_in< streamSt<Config> > streamIn;


    dutBase(std::string name, const char * variant) :
        streamOut("streamOut")
        ,streamIn("streamIn")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        streamOut->setTimed(nsec, mode);
        streamIn->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        streamOut->setLogging(verbosity);
        streamIn->setLogging(verbosity);
    };
    using streamDataT = streamDataT<Config>;
    using streamSt = streamSt<Config>;
};
export template<typename Config>
class dutInverted : public virtual blockPortBase
{
public:
    // src ports
    // dutStreamIf->uSink: Parameterized DUT stream (also the connection interface A)
    push_ack_in< streamSt<Config> > streamOut;

    // dst ports
    // uSrc->dutStreamIf: Parameterized DUT stream (also the connection interface A)
    push_ack_out< streamSt<Config> > streamIn;


    dutInverted(std::string name) :
        streamOut(("streamOut"+name).c_str())
        ,streamIn(("streamIn"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        streamOut->setTimed(nsec, mode);
        streamIn->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        streamOut->setLogging(verbosity);
        streamIn->setLogging(verbosity);
    };
};
export template<typename Config>
class dutChannels
{
public:
    // src ports
    // Parameterized DUT stream (also the connection interface A)
    push_ack_channel< streamSt<Config> > streamOut;

    // dst ports
    // Parameterized DUT stream (also the connection interface A)
    push_ack_channel< streamSt<Config> > streamIn;


    dutChannels(std::string name, std::string srcName) :
    streamOut(("streamOut"+name).c_str(), srcName)
    ,streamIn(("streamIn"+name).c_str(), srcName)
    {};
    void bind( dutBase<Config> *a, dutInverted<Config> *b)
    {
        a->streamOut( streamOut );
        b->streamOut( streamOut );
        a->streamIn( streamIn );
        b->streamIn( streamIn );
    };
};

// GENERATED_CODE_END
