//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipStdMaster --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"

export module ip_ipStdMaster.base;
import ip;
using namespace ip_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class ipStdMasterBase : public virtual blockPortBase
{
public:
    virtual ~ipStdMasterBase() = default;
    // src ports
    // ipReg->uIpStdDecode: Register bus the ip block consumes
    apb_out< ipRegAddrSt, ipRegDataSt > apbOut;


    ipStdMasterBase(std::string name, const char * variant) :
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
export class ipStdMasterInverted : public virtual blockPortBase
{
public:
    // src ports
    // ipReg->uIpStdDecode: Register bus the ip block consumes
    apb_in< ipRegAddrSt, ipRegDataSt > apbOut;


    ipStdMasterInverted(std::string name) :
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
export class ipStdMasterChannels
{
public:
    // src ports
    // Register bus the ip block consumes
    apb_channel< ipRegAddrSt, ipRegDataSt > apbOut;


    ipStdMasterChannels(std::string name, std::string srcName) :
    apbOut(("apbOut"+name).c_str(), srcName)
    {};
    void bind( ipStdMasterBase *a, ipStdMasterInverted *b)
    {
        a->apbOut( apbOut );
        b->apbOut( apbOut );
    };
};

// GENERATED_CODE_END
