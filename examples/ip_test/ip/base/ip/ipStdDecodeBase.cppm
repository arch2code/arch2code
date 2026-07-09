//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipStdDecode --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"

export module ipStdDecode.base;
import ip;
using namespace ip_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class ipStdDecodeBase : public virtual blockPortBase
{
public:
    virtual ~ipStdDecodeBase() = default;
    // src ports
    // ipReg->uIp: Register bus the ip block consumes
    apb_out< ipRegAddrSt, ipRegDataSt > ipReg_uIp;

    // dst ports
    // uIpStdMaster->ipReg: Register bus the ip block consumes
    apb_in< ipRegAddrSt, ipRegDataSt > ipReg;


    ipStdDecodeBase(std::string name, const char * variant) :
        ipReg_uIp("ipReg_uIp")
        ,ipReg("ipReg")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        ipReg_uIp->setTimed(nsec, mode);
        ipReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        ipReg_uIp->setLogging(verbosity);
        ipReg->setLogging(verbosity);
    };
};
export class ipStdDecodeInverted : public virtual blockPortBase
{
public:
    // src ports
    // ipReg->uIp: Register bus the ip block consumes
    apb_in< ipRegAddrSt, ipRegDataSt > ipReg_uIp;

    // dst ports
    // uIpStdMaster->ipReg: Register bus the ip block consumes
    apb_out< ipRegAddrSt, ipRegDataSt > ipReg;


    ipStdDecodeInverted(std::string name) :
        ipReg_uIp(("ipReg_uIp"+name).c_str())
        ,ipReg(("ipReg"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        ipReg_uIp->setTimed(nsec, mode);
        ipReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        ipReg_uIp->setLogging(verbosity);
        ipReg->setLogging(verbosity);
    };
};
export class ipStdDecodeChannels
{
public:
    // src ports
    // Register bus the ip block consumes
    apb_channel< ipRegAddrSt, ipRegDataSt > ipReg_uIp;

    // dst ports
    // Register bus the ip block consumes
    apb_channel< ipRegAddrSt, ipRegDataSt > ipReg;


    ipStdDecodeChannels(std::string name, std::string srcName) :
    ipReg_uIp(("ipReg_uIp"+name).c_str(), srcName)
    ,ipReg(("ipReg"+name).c_str(), srcName)
    {};
    void bind( ipStdDecodeBase *a, ipStdDecodeInverted *b)
    {
        a->ipReg_uIp( ipReg_uIp );
        b->ipReg_uIp( ipReg_uIp );
        a->ipReg( ipReg );
        b->ipReg( ipReg );
    };
};

// GENERATED_CODE_END
