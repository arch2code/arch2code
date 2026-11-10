//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=leafA --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "ahb_channel.h"

export module ahbDecode_leafA.base;
import ahbDecode;
using namespace ahbDecode_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class leafABase : public virtual blockPortBase
{
public:
    virtual ~leafABase() = default;
    // dst ports
    // uRouter->ahbReg: CPU access to the registers in the design
    ahb_in< ahbAddrSt, ahbDataSt > ahbReg;


    leafABase(std::string name, const char * variant) :
        ahbReg("ahbReg")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        ahbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        ahbReg->setLogging(verbosity);
    };
};
export class leafAInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uRouter->ahbReg: CPU access to the registers in the design
    ahb_out< ahbAddrSt, ahbDataSt > ahbReg;


    leafAInverted(std::string name) :
        ahbReg(("ahbReg"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        ahbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        ahbReg->setLogging(verbosity);
    };
};
export class leafAChannels
{
public:
    // dst ports
    // CPU access to the registers in the design
    ahb_channel< ahbAddrSt, ahbDataSt > ahbReg;


    leafAChannels(std::string name, std::string srcName) :
    ahbReg(("ahbReg"+name).c_str(), srcName)
    {};
    void bind( leafABase *a, leafAInverted *b)
    {
        a->ahbReg( ahbReg );
        b->ahbReg( ahbReg );
    };
};

// GENERATED_CODE_END
