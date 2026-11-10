//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ahbRouter --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "ahb_channel.h"

export module ahbDecode_ahbRouter.base;
import ahbDecode;
using namespace ahbDecode_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class ahbRouterBase : public virtual blockPortBase
{
public:
    virtual ~ahbRouterBase() = default;
    // src ports
    // ahbReg->uLeafA: CPU access to the registers in the design
    ahb_out< ahbAddrSt, ahbDataSt > ahbReg_uLeafA;
    // ahbReg->uLeafB: CPU access to the registers in the design
    ahb_out< ahbAddrSt, ahbDataSt > ahbReg_uLeafB;
    // ahbReg->uSubSys: CPU access to the registers in the design
    ahb_out< ahbAddrSt, ahbDataSt > ahbReg_uSubSys;

    // dst ports
    // External->ahbReg: CPU access to the registers in the design
    ahb_in< ahbAddrSt, ahbDataSt > ahbReg;


    ahbRouterBase(std::string name, const char * variant) :
        ahbReg_uLeafA("ahbReg_uLeafA")
        ,ahbReg_uLeafB("ahbReg_uLeafB")
        ,ahbReg_uSubSys("ahbReg_uSubSys")
        ,ahbReg("ahbReg")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        ahbReg_uLeafA->setTimed(nsec, mode);
        ahbReg_uLeafB->setTimed(nsec, mode);
        ahbReg_uSubSys->setTimed(nsec, mode);
        ahbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        ahbReg_uLeafA->setLogging(verbosity);
        ahbReg_uLeafB->setLogging(verbosity);
        ahbReg_uSubSys->setLogging(verbosity);
        ahbReg->setLogging(verbosity);
    };
};
export class ahbRouterInverted : public virtual blockPortBase
{
public:
    // src ports
    // ahbReg->uLeafA: CPU access to the registers in the design
    ahb_in< ahbAddrSt, ahbDataSt > ahbReg_uLeafA;
    // ahbReg->uLeafB: CPU access to the registers in the design
    ahb_in< ahbAddrSt, ahbDataSt > ahbReg_uLeafB;
    // ahbReg->uSubSys: CPU access to the registers in the design
    ahb_in< ahbAddrSt, ahbDataSt > ahbReg_uSubSys;

    // dst ports
    // External->ahbReg: CPU access to the registers in the design
    ahb_out< ahbAddrSt, ahbDataSt > ahbReg;


    ahbRouterInverted(std::string name) :
        ahbReg_uLeafA(("ahbReg_uLeafA"+name).c_str())
        ,ahbReg_uLeafB(("ahbReg_uLeafB"+name).c_str())
        ,ahbReg_uSubSys(("ahbReg_uSubSys"+name).c_str())
        ,ahbReg(("ahbReg"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        ahbReg_uLeafA->setTimed(nsec, mode);
        ahbReg_uLeafB->setTimed(nsec, mode);
        ahbReg_uSubSys->setTimed(nsec, mode);
        ahbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        ahbReg_uLeafA->setLogging(verbosity);
        ahbReg_uLeafB->setLogging(verbosity);
        ahbReg_uSubSys->setLogging(verbosity);
        ahbReg->setLogging(verbosity);
    };
};
export class ahbRouterChannels
{
public:
    // src ports
    // CPU access to the registers in the design
    ahb_channel< ahbAddrSt, ahbDataSt > ahbReg_uLeafA;
    // CPU access to the registers in the design
    ahb_channel< ahbAddrSt, ahbDataSt > ahbReg_uLeafB;
    // CPU access to the registers in the design
    ahb_channel< ahbAddrSt, ahbDataSt > ahbReg_uSubSys;

    // dst ports
    // CPU access to the registers in the design
    ahb_channel< ahbAddrSt, ahbDataSt > ahbReg;


    ahbRouterChannels(std::string name, std::string srcName) :
    ahbReg_uLeafA(("ahbReg_uLeafA"+name).c_str(), srcName)
    ,ahbReg_uLeafB(("ahbReg_uLeafB"+name).c_str(), srcName)
    ,ahbReg_uSubSys(("ahbReg_uSubSys"+name).c_str(), srcName)
    ,ahbReg(("ahbReg"+name).c_str(), srcName)
    {};
    void bind( ahbRouterBase *a, ahbRouterInverted *b)
    {
        a->ahbReg_uLeafA( ahbReg_uLeafA );
        b->ahbReg_uLeafA( ahbReg_uLeafA );
        a->ahbReg_uLeafB( ahbReg_uLeafB );
        b->ahbReg_uLeafB( ahbReg_uLeafB );
        a->ahbReg_uSubSys( ahbReg_uSubSys );
        b->ahbReg_uSubSys( ahbReg_uSubSys );
        a->ahbReg( ahbReg );
        b->ahbReg( ahbReg );
    };
};

// GENERATED_CODE_END
