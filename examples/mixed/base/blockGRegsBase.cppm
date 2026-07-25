//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockGRegs --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"
#include "status_channel.h"

export module blockGRegs.base;
import mixed;
using namespace mixed_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class blockGRegsBase : public virtual blockPortBase
{
public:
    virtual ~blockGRegsBase() = default;
    static constexpr auto fred = Config::fred;
    // src ports
    // blockG->reg(rwG) A Read Write register owned by parameterized container blockG and forwarded to a leaf
    status_out< dRegSt > rwG;

    // dst ports
    // External->apbReg: CPU access to SoC registers in the design
    apb_in< apbAddrSt, apbDataSt > apbReg;


    blockGRegsBase(std::string name, const char * variant) :
        rwG("rwG")
        ,apbReg("apbReg")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        rwG->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        rwG->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
};
export template<typename Config>
class blockGRegsInverted : public virtual blockPortBase
{
public:
    // src ports
    // blockG->reg(rwG) A Read Write register owned by parameterized container blockG and forwarded to a leaf
    status_in< dRegSt > rwG;

    // dst ports
    // External->apbReg: CPU access to SoC registers in the design
    apb_out< apbAddrSt, apbDataSt > apbReg;


    blockGRegsInverted(std::string name) :
        rwG(("rwG"+name).c_str())
        ,apbReg(("apbReg"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        rwG->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        rwG->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
};
export template<typename Config>
class blockGRegsChannels
{
public:
    // src ports
    // A Read Write register owned by parameterized container blockG and forwarded to a leaf
    status_channel< dRegSt > rwG;

    // dst ports
    // CPU access to SoC registers in the design
    apb_channel< apbAddrSt, apbDataSt > apbReg;


    blockGRegsChannels(std::string name, std::string srcName) :
    rwG(("rwG"+name).c_str(), srcName)
    ,apbReg(("apbReg"+name).c_str(), srcName)
    {};
    void bind( blockGRegsBase<Config> *a, blockGRegsInverted<Config> *b)
    {
        a->rwG( rwG );
        b->rwG( rwG );
        a->apbReg( apbReg );
        b->apbReg( apbReg );
    };
};

// GENERATED_CODE_END
