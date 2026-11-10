//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=subRouter --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "ahb_channel.h"

export module ahbDecode_subRouter.base;
import ahbDecode;
using namespace ahbDecode_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class subRouterBase : public virtual blockPortBase
{
public:
    virtual ~subRouterBase() = default;
    // src ports
    // ahbReg->uLeafC: CPU access to the registers in the design
    ahb_out< ahbAddrSt, ahbDataSt > ahbReg_uLeafC;

    // dst ports
    // External->ahbReg: CPU access to the registers in the design
    ahb_in< ahbAddrSt, ahbDataSt > ahbReg;


    subRouterBase(std::string name, const char * variant) :
        ahbReg_uLeafC("ahbReg_uLeafC")
        ,ahbReg("ahbReg")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        ahbReg_uLeafC->setTimed(nsec, mode);
        ahbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        ahbReg_uLeafC->setLogging(verbosity);
        ahbReg->setLogging(verbosity);
    };
};
export class subRouterInverted : public virtual blockPortBase
{
public:
    // src ports
    // ahbReg->uLeafC: CPU access to the registers in the design
    ahb_in< ahbAddrSt, ahbDataSt > ahbReg_uLeafC;

    // dst ports
    // External->ahbReg: CPU access to the registers in the design
    ahb_out< ahbAddrSt, ahbDataSt > ahbReg;


    subRouterInverted(std::string name) :
        ahbReg_uLeafC(("ahbReg_uLeafC"+name).c_str())
        ,ahbReg(("ahbReg"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        ahbReg_uLeafC->setTimed(nsec, mode);
        ahbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        ahbReg_uLeafC->setLogging(verbosity);
        ahbReg->setLogging(verbosity);
    };
};
export class subRouterChannels
{
public:
    // src ports
    // CPU access to the registers in the design
    ahb_channel< ahbAddrSt, ahbDataSt > ahbReg_uLeafC;

    // dst ports
    // CPU access to the registers in the design
    ahb_channel< ahbAddrSt, ahbDataSt > ahbReg;


    subRouterChannels(std::string name, std::string srcName) :
    ahbReg_uLeafC(("ahbReg_uLeafC"+name).c_str(), srcName)
    ,ahbReg(("ahbReg"+name).c_str(), srcName)
    {};
    void bind( subRouterBase *a, subRouterInverted *b)
    {
        a->ahbReg_uLeafC( ahbReg_uLeafC );
        b->ahbReg_uLeafC( ahbReg_uLeafC );
        a->ahbReg( ahbReg );
        b->ahbReg( ahbReg );
    };
};

// GENERATED_CODE_END
