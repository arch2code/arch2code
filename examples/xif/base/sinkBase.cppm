//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=sink --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module sink.base;
import xif;
using namespace xif_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class sinkBase : public virtual blockPortBase
{
public:
    virtual ~sinkBase() = default;
    static constexpr auto DATA_WIDTH = Config::DATA_WIDTH;
    static constexpr auto FRAME_HEIGHT = Config::FRAME_HEIGHT;
    static constexpr auto FRAME_WIDTH = Config::FRAME_WIDTH;
    // dst ports
    // uDut->streamBndryIf: Non-parameterized boundary interface B (differing name) declared on the edge ports
    push_ack_in< streamBndrySt > in;


    sinkBase(std::string name, const char * variant) :
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
    using streamDataT = streamDataT<Config>;
    using streamSt = streamSt<Config>;
};
export template<typename Config>
class sinkInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uDut->streamBndryIf: Non-parameterized boundary interface B (differing name) declared on the edge ports
    push_ack_out< streamBndrySt > in;


    sinkInverted(std::string name) :
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
class sinkChannels
{
public:
    // dst ports
    // Non-parameterized boundary interface B (differing name) declared on the edge ports
    push_ack_channel< streamBndrySt > in;


    sinkChannels(std::string name, std::string srcName) :
    in(("in"+name).c_str(), srcName)
    {};
    void bind( sinkBase<Config> *a, sinkInverted<Config> *b)
    {
        a->in( in );
        b->in( in );
    };
};

// GENERATED_CODE_END
