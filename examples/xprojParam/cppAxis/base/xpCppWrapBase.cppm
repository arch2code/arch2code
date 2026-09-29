//

// GENERATED_CODE_PARAM --block=xpCppWrap --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpCppAxis_xpCppWrap.base;
import xpCppAxis_xpCppWrap;
import xpCppLeaf;
using namespace xpCppAxis_xpCppWrap_ns;
using namespace xpCppLeaf_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpCppWrapBase : public virtual blockPortBase
{
public:
    virtual ~xpCppWrapBase() = default;
    static constexpr auto WRAP_PIXEL_WIDTH = Config::WRAP_PIXEL_WIDTH;
    // dst ports
    // uDrive->wrapEqIf: Wrapper stream whose members correspond to the IP's
    push_ack_in< wrapEqSt<Config> > eqIn;
    // uDrive->wrapOrderIf: Wrapper stream whose member storage order is the IP's reversed
    push_ack_in< wrapOrderSt<Config> > orderIn;
    // uDrive->wrapSignIf: Unsigned wrapper stream against the IP's signed one
    push_ack_in< wrapSignSt<Config> > signIn;
    // uDrive->wrapNestIf: Nested wrapper stream against the IP's flat one
    push_ack_in< wrapNestSt<Config> > nestIn;


    xpCppWrapBase(std::string name, const char * variant) :
        eqIn("eqIn")
        ,orderIn("orderIn")
        ,signIn("signIn")
        ,nestIn("nestIn")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        eqIn->setTimed(nsec, mode);
        orderIn->setTimed(nsec, mode);
        signIn->setTimed(nsec, mode);
        nestIn->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        eqIn->setLogging(verbosity);
        orderIn->setLogging(verbosity);
        signIn->setLogging(verbosity);
        nestIn->setLogging(verbosity);
    };
    using wrapPixelT = wrapPixelT<Config>;
    using wrapEqSt = wrapEqSt<Config>;
    using wrapOrderSt = wrapOrderSt<Config>;
    using wrapSignSt = wrapSignSt<Config>;
    using wrapNestSt = wrapNestSt<Config>;
};
export template<typename Config>
class xpCppWrapInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uDrive->wrapEqIf: Wrapper stream whose members correspond to the IP's
    push_ack_out< wrapEqSt<Config> > eqIn;
    // uDrive->wrapOrderIf: Wrapper stream whose member storage order is the IP's reversed
    push_ack_out< wrapOrderSt<Config> > orderIn;
    // uDrive->wrapSignIf: Unsigned wrapper stream against the IP's signed one
    push_ack_out< wrapSignSt<Config> > signIn;
    // uDrive->wrapNestIf: Nested wrapper stream against the IP's flat one
    push_ack_out< wrapNestSt<Config> > nestIn;


    xpCppWrapInverted(std::string name) :
        eqIn(("eqIn"+name).c_str())
        ,orderIn(("orderIn"+name).c_str())
        ,signIn(("signIn"+name).c_str())
        ,nestIn(("nestIn"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        eqIn->setTimed(nsec, mode);
        orderIn->setTimed(nsec, mode);
        signIn->setTimed(nsec, mode);
        nestIn->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        eqIn->setLogging(verbosity);
        orderIn->setLogging(verbosity);
        signIn->setLogging(verbosity);
        nestIn->setLogging(verbosity);
    };
};
export template<typename Config>
class xpCppWrapChannels
{
public:
    // dst ports
    // Wrapper stream whose members correspond to the IP's
    push_ack_channel< wrapEqSt<Config> > eqIn;
    // Wrapper stream whose member storage order is the IP's reversed
    push_ack_channel< wrapOrderSt<Config> > orderIn;
    // Unsigned wrapper stream against the IP's signed one
    push_ack_channel< wrapSignSt<Config> > signIn;
    // Nested wrapper stream against the IP's flat one
    push_ack_channel< wrapNestSt<Config> > nestIn;


    xpCppWrapChannels(std::string name, std::string srcName) :
    eqIn(("eqIn"+name).c_str(), srcName)
    ,orderIn(("orderIn"+name).c_str(), srcName)
    ,signIn(("signIn"+name).c_str(), srcName)
    ,nestIn(("nestIn"+name).c_str(), srcName)
    {};
    void bind( xpCppWrapBase<Config> *a, xpCppWrapInverted<Config> *b)
    {
        a->eqIn( eqIn );
        b->eqIn( eqIn );
        a->orderIn( orderIn );
        b->orderIn( orderIn );
        a->signIn( signIn );
        b->signIn( signIn );
        a->nestIn( nestIn );
        b->nestIn( nestIn );
    };
};

// GENERATED_CODE_END
