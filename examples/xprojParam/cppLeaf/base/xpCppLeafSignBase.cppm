//

// GENERATED_CODE_PARAM --block=xpCppLeafSign --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpCppLeaf_xpCppLeafSign.base;
import xpCppLeaf;
using namespace xpCppLeaf_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpCppLeafSignBase : public virtual blockPortBase
{
public:
    virtual ~xpCppLeafSignBase() = default;
    static constexpr auto LEAF_PIXEL_WIDTH = Config::LEAF_PIXEL_WIDTH;
    // dst ports
    // External->leafSignIf: Signed parameterizable stream
    push_ack_in< leafSignSt<Config> > signIn;


    xpCppLeafSignBase(std::string name, const char * variant) :
        signIn("signIn")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        signIn->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        signIn->setLogging(verbosity);
    };
    using leafPixelT = leafPixelT<Config>;
    using leafSignedPixelT = leafSignedPixelT<Config>;
    using leafEqSt = leafEqSt<Config>;
    using leafOrderSt = leafOrderSt<Config>;
    using leafSignSt = leafSignSt<Config>;
    using leafNestSt = leafNestSt<Config>;
};
export template<typename Config>
class xpCppLeafSignInverted : public virtual blockPortBase
{
public:
    // dst ports
    // External->leafSignIf: Signed parameterizable stream
    push_ack_out< leafSignSt<Config> > signIn;


    xpCppLeafSignInverted(std::string name) :
        signIn(("signIn"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        signIn->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        signIn->setLogging(verbosity);
    };
};
export template<typename Config>
class xpCppLeafSignChannels
{
public:
    // dst ports
    // Signed parameterizable stream
    push_ack_channel< leafSignSt<Config> > signIn;


    xpCppLeafSignChannels(std::string name, std::string srcName) :
    signIn(("signIn"+name).c_str(), srcName)
    {};
    void bind( xpCppLeafSignBase<Config> *a, xpCppLeafSignInverted<Config> *b)
    {
        a->signIn( signIn );
        b->signIn( signIn );
    };
};

// GENERATED_CODE_END
