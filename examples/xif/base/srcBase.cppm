//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=src --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xif_src.base;
import xif;
using namespace xif_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class srcBase : public virtual blockPortBase
{
public:
    virtual ~srcBase() = default;
    static constexpr auto DATA_WIDTH = Config::DATA_WIDTH;
    static constexpr auto FRAME_HEIGHT = Config::FRAME_HEIGHT;
    static constexpr auto FRAME_WIDTH = Config::FRAME_WIDTH;
    // src ports
    // streamBndryIf->uDut: Non-parameterized boundary interface B (differing name) declared on the edge ports
    push_ack_out< streamBndrySt > out;


    srcBase(std::string name, const char * variant) :
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
    using streamDataT = streamDataT<Config>;
    using streamSt = streamSt<Config>;
};
export template<typename Config>
class srcInverted : public virtual blockPortBase
{
public:
    // src ports
    // streamBndryIf->uDut: Non-parameterized boundary interface B (differing name) declared on the edge ports
    push_ack_in< streamBndrySt > out;


    srcInverted(std::string name) :
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
class srcChannels
{
public:
    // src ports
    // Non-parameterized boundary interface B (differing name) declared on the edge ports
    push_ack_channel< streamBndrySt > out;


    srcChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName)
    {};
    void bind( srcBase<Config> *a, srcInverted<Config> *b)
    {
        a->out( out );
        b->out( out );
    };
};

// GENERATED_CODE_END
