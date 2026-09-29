//

// GENERATED_CODE_PARAM --block=cppDriver --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpCppAxis_cppDriver.base;
import xpCppAxis_xpCppAxisTop;
using namespace xpCppAxis_xpCppAxisTop_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class cppDriverBase : public virtual blockPortBase
{
public:
    virtual ~cppDriverBase() = default;
    // src ports
    // bndEqIf->uWrap: Literal-width boundary stream into the wrapper's corresponding port
    push_ack_out< bndEqSt > eqOut;
    // bndOrderIf->uWrap: Literal-width boundary stream into the wrapper's reversed-storage port
    push_ack_out< bndOrderSt > orderOut;
    // bndSignIf->uWrap: Literal-width boundary stream into the wrapper's unsigned port
    push_ack_out< bndSignSt > signOut;
    // bndNestIf->uWrap: Literal-width boundary stream into the wrapper's nested port
    push_ack_out< bndNestSt > nestOut;


    cppDriverBase(std::string name, const char * variant) :
        eqOut("eqOut")
        ,orderOut("orderOut")
        ,signOut("signOut")
        ,nestOut("nestOut")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        eqOut->setTimed(nsec, mode);
        orderOut->setTimed(nsec, mode);
        signOut->setTimed(nsec, mode);
        nestOut->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        eqOut->setLogging(verbosity);
        orderOut->setLogging(verbosity);
        signOut->setLogging(verbosity);
        nestOut->setLogging(verbosity);
    };
};
export class cppDriverInverted : public virtual blockPortBase
{
public:
    // src ports
    // bndEqIf->uWrap: Literal-width boundary stream into the wrapper's corresponding port
    push_ack_in< bndEqSt > eqOut;
    // bndOrderIf->uWrap: Literal-width boundary stream into the wrapper's reversed-storage port
    push_ack_in< bndOrderSt > orderOut;
    // bndSignIf->uWrap: Literal-width boundary stream into the wrapper's unsigned port
    push_ack_in< bndSignSt > signOut;
    // bndNestIf->uWrap: Literal-width boundary stream into the wrapper's nested port
    push_ack_in< bndNestSt > nestOut;


    cppDriverInverted(std::string name) :
        eqOut(("eqOut"+name).c_str())
        ,orderOut(("orderOut"+name).c_str())
        ,signOut(("signOut"+name).c_str())
        ,nestOut(("nestOut"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        eqOut->setTimed(nsec, mode);
        orderOut->setTimed(nsec, mode);
        signOut->setTimed(nsec, mode);
        nestOut->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        eqOut->setLogging(verbosity);
        orderOut->setLogging(verbosity);
        signOut->setLogging(verbosity);
        nestOut->setLogging(verbosity);
    };
};
export class cppDriverChannels
{
public:
    // src ports
    // Literal-width boundary stream into the wrapper's corresponding port
    push_ack_channel< bndEqSt > eqOut;
    // Literal-width boundary stream into the wrapper's reversed-storage port
    push_ack_channel< bndOrderSt > orderOut;
    // Literal-width boundary stream into the wrapper's unsigned port
    push_ack_channel< bndSignSt > signOut;
    // Literal-width boundary stream into the wrapper's nested port
    push_ack_channel< bndNestSt > nestOut;


    cppDriverChannels(std::string name, std::string srcName) :
    eqOut(("eqOut"+name).c_str(), srcName)
    ,orderOut(("orderOut"+name).c_str(), srcName)
    ,signOut(("signOut"+name).c_str(), srcName)
    ,nestOut(("nestOut"+name).c_str(), srcName)
    {};
    void bind( cppDriverBase *a, cppDriverInverted *b)
    {
        a->eqOut( eqOut );
        b->eqOut( eqOut );
        a->orderOut( orderOut );
        b->orderOut( orderOut );
        a->signOut( signOut );
        b->signOut( signOut );
        a->nestOut( nestOut );
        b->nestOut( nestOut );
    };
};

// GENERATED_CODE_END
