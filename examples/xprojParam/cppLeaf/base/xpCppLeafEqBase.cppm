//

// GENERATED_CODE_PARAM --block=xpCppLeafEq --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpCppLeaf_xpCppLeafEq.base;
import xpCppLeaf;
using namespace xpCppLeaf_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpCppLeafEqBase : public virtual blockPortBase
{
public:
    virtual ~xpCppLeafEqBase() = default;
    static constexpr auto LEAF_PIXEL_WIDTH = Config::LEAF_PIXEL_WIDTH;
    // dst ports
    // External->leafEqIf: Parameterizable stream whose members correspond to the wrapper's
    push_ack_in< leafEqSt<Config> > eqIn;


    xpCppLeafEqBase(std::string name, const char * variant) :
        eqIn("eqIn")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        eqIn->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        eqIn->setLogging(verbosity);
    };
    using leafPixelT = leafPixelT<Config>;
    using leafSignedPixelT = leafSignedPixelT<Config>;
    using leafEqSt = leafEqSt<Config>;
    using leafOrderSt = leafOrderSt<Config>;
    using leafSignSt = leafSignSt<Config>;
    using leafNestSt = leafNestSt<Config>;
};
export template<typename Config>
class xpCppLeafEqInverted : public virtual blockPortBase
{
public:
    // dst ports
    // External->leafEqIf: Parameterizable stream whose members correspond to the wrapper's
    push_ack_out< leafEqSt<Config> > eqIn;


    xpCppLeafEqInverted(std::string name) :
        eqIn(("eqIn"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        eqIn->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        eqIn->setLogging(verbosity);
    };
};
export template<typename Config>
class xpCppLeafEqChannels
{
public:
    // dst ports
    // Parameterizable stream whose members correspond to the wrapper's
    push_ack_channel< leafEqSt<Config> > eqIn;


    xpCppLeafEqChannels(std::string name, std::string srcName) :
    eqIn(("eqIn"+name).c_str(), srcName)
    {};
    void bind( xpCppLeafEqBase<Config> *a, xpCppLeafEqInverted<Config> *b)
    {
        a->eqIn( eqIn );
        b->eqIn( eqIn );
    };
};

// GENERATED_CODE_END
