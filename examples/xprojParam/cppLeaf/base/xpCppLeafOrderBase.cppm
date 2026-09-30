//

// GENERATED_CODE_PARAM --block=xpCppLeafOrder --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpCppLeaf_xpCppLeafOrder.base;
import xpCppLeaf;
using namespace xpCppLeaf_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpCppLeafOrderBase : public virtual blockPortBase
{
public:
    virtual ~xpCppLeafOrderBase() = default;
    static constexpr auto LEAF_PIXEL_WIDTH = Config::LEAF_PIXEL_WIDTH;
    // dst ports
    // External->leafOrderIf: Parameterizable stream whose member storage order is the wrapper's reversed
    push_ack_in< leafOrderSt<Config> > orderIn;


    xpCppLeafOrderBase(std::string name, const char * variant) :
        orderIn("orderIn")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        orderIn->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        orderIn->setLogging(verbosity);
    };
    using leafPixelT = leafPixelT<Config>;
    using leafSignedPixelT = leafSignedPixelT<Config>;
    using leafEqSt = leafEqSt<Config>;
    using leafOrderSt = leafOrderSt<Config>;
    using leafSignSt = leafSignSt<Config>;
    using leafNestSt = leafNestSt<Config>;
};
export template<typename Config>
class xpCppLeafOrderInverted : public virtual blockPortBase
{
public:
    // dst ports
    // External->leafOrderIf: Parameterizable stream whose member storage order is the wrapper's reversed
    push_ack_out< leafOrderSt<Config> > orderIn;


    xpCppLeafOrderInverted(std::string name) :
        orderIn(("orderIn"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        orderIn->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        orderIn->setLogging(verbosity);
    };
};
export template<typename Config>
class xpCppLeafOrderChannels
{
public:
    // dst ports
    // Parameterizable stream whose member storage order is the wrapper's reversed
    push_ack_channel< leafOrderSt<Config> > orderIn;


    xpCppLeafOrderChannels(std::string name, std::string srcName) :
    orderIn(("orderIn"+name).c_str(), srcName)
    {};
    void bind( xpCppLeafOrderBase<Config> *a, xpCppLeafOrderInverted<Config> *b)
    {
        a->orderIn( orderIn );
        b->orderIn( orderIn );
    };
};

// GENERATED_CODE_END
