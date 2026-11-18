//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ahbSoc --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "ahb_channel.h"

export module ahbDecode_ahbSoc.base;
import ahbDecode;
using namespace ahbDecode_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class ahbSocBase : public virtual blockPortBase
{
public:
    virtual ~ahbSocBase() = default;
    // dst ports
    // uCPU->ahbReg: CPU access to the registers in the design
    ahb_in< ahbAddrSt, ahbDataSt > ahbReg;


    ahbSocBase(std::string name, const char * variant) :
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
export class ahbSocInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uCPU->ahbReg: CPU access to the registers in the design
    ahb_out< ahbAddrSt, ahbDataSt > ahbReg;


    ahbSocInverted(std::string name) :
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
export class ahbSocChannels
{
public:
    // dst ports
    // CPU access to the registers in the design
    ahb_channel< ahbAddrSt, ahbDataSt > ahbReg;


    ahbSocChannels(std::string name, std::string srcName) :
    ahbReg(("ahbReg"+name).c_str(), srcName)
    {};
    void bind( ahbSocBase *a, ahbSocInverted *b)
    {
        a->ahbReg( ahbReg );
        b->ahbReg( ahbReg );
    };
};

// GENERATED_CODE_END
