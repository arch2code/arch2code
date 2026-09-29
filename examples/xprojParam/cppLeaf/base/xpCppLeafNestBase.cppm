//

// GENERATED_CODE_PARAM --block=xpCppLeafNest --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpCppLeaf_xpCppLeafNest.base;
import xpCppLeaf;
using namespace xpCppLeaf_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpCppLeafNestBase : public virtual blockPortBase
{
public:
    virtual ~xpCppLeafNestBase() = default;
    static constexpr auto LEAF_PIXEL_WIDTH = Config::LEAF_PIXEL_WIDTH;
    // dst ports
    // External->leafNestIf: Flat parameterizable stream matching the wrapper's nested layout
    push_ack_in< leafNestSt<Config> > nestIn;


    xpCppLeafNestBase(std::string name, const char * variant) :
        nestIn("nestIn")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        nestIn->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        nestIn->setLogging(verbosity);
    };
    using leafPixelT = leafPixelT<Config>;
    using leafSignedPixelT = leafSignedPixelT<Config>;
    using leafEqSt = leafEqSt<Config>;
    using leafOrderSt = leafOrderSt<Config>;
    using leafSignSt = leafSignSt<Config>;
    using leafNestSt = leafNestSt<Config>;
};
export template<typename Config>
class xpCppLeafNestInverted : public virtual blockPortBase
{
public:
    // dst ports
    // External->leafNestIf: Flat parameterizable stream matching the wrapper's nested layout
    push_ack_out< leafNestSt<Config> > nestIn;


    xpCppLeafNestInverted(std::string name) :
        nestIn(("nestIn"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        nestIn->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        nestIn->setLogging(verbosity);
    };
};
export template<typename Config>
class xpCppLeafNestChannels
{
public:
    // dst ports
    // Flat parameterizable stream matching the wrapper's nested layout
    push_ack_channel< leafNestSt<Config> > nestIn;


    xpCppLeafNestChannels(std::string name, std::string srcName) :
    nestIn(("nestIn"+name).c_str(), srcName)
    {};
    void bind( xpCppLeafNestBase<Config> *a, xpCppLeafNestInverted<Config> *b)
    {
        a->nestIn( nestIn );
        b->nestIn( nestIn );
    };
};

// GENERATED_CODE_END
