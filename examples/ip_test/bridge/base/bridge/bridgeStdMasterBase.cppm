//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=bridgeStdMaster --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"

export module bridgeStdMaster.base;
import shared_types;
using namespace shared_types_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class bridgeStdMasterBase : public virtual blockPortBase
{
public:
    virtual ~bridgeStdMasterBase() = default;
    // src ports
    // apbReg->uBridge: CPU access to registers via APB
    apb_out< apbAddrSt, apbDataSt > apbOut;


    bridgeStdMasterBase(std::string name, const char * variant) :
        apbOut("apbOut")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbOut->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbOut->setLogging(verbosity);
    };
};
export class bridgeStdMasterInverted : public virtual blockPortBase
{
public:
    // src ports
    // apbReg->uBridge: CPU access to registers via APB
    apb_in< apbAddrSt, apbDataSt > apbOut;


    bridgeStdMasterInverted(std::string name) :
        apbOut(("apbOut"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbOut->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbOut->setLogging(verbosity);
    };
};
export class bridgeStdMasterChannels
{
public:
    // src ports
    // CPU access to registers via APB
    apb_channel< apbAddrSt, apbDataSt > apbOut;


    bridgeStdMasterChannels(std::string name, std::string srcName) :
    apbOut(("apbOut"+name).c_str(), srcName)
    {};
    void bind( bridgeStdMasterBase *a, bridgeStdMasterInverted *b)
    {
        a->apbOut( apbOut );
        b->apbOut( apbOut );
    };
};

// GENERATED_CODE_END
