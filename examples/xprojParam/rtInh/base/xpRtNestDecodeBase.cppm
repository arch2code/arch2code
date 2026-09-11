//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=xpRtNestDecode --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"

export module xpRtInh_xpRtNestDecode.base;
import common_shared_types;
import xpRtInh;
using namespace common_shared_types_ns;
using namespace xpRtInh_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpRtNestDecodeBase : public virtual blockPortBase
{
public:
    virtual ~xpRtNestDecodeBase() = default;
    static constexpr auto RT_WIDTH = Config::RT_WIDTH;
    // src ports
    // apbReg->uLeaf: CPU access to registers via APB
    apb_out< apbAddrSt, apbDataSt > apbReg_uLeaf;

    // dst ports
    // External->apbReg: CPU access to registers via APB
    apb_in< apbAddrSt, apbDataSt > apbReg;


    xpRtNestDecodeBase(std::string name, const char * variant) :
        apbReg_uLeaf("apbReg_uLeaf")
        ,apbReg("apbReg")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbReg_uLeaf->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbReg_uLeaf->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
    using cfgDataT = cfgDataT<Config>;
    using cfgSt = cfgSt<Config>;
};
export template<typename Config>
class xpRtNestDecodeInverted : public virtual blockPortBase
{
public:
    // src ports
    // apbReg->uLeaf: CPU access to registers via APB
    apb_in< apbAddrSt, apbDataSt > apbReg_uLeaf;

    // dst ports
    // External->apbReg: CPU access to registers via APB
    apb_out< apbAddrSt, apbDataSt > apbReg;


    xpRtNestDecodeInverted(std::string name) :
        apbReg_uLeaf(("apbReg_uLeaf"+name).c_str())
        ,apbReg(("apbReg"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbReg_uLeaf->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbReg_uLeaf->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
};
export template<typename Config>
class xpRtNestDecodeChannels
{
public:
    // src ports
    // CPU access to registers via APB
    apb_channel< apbAddrSt, apbDataSt > apbReg_uLeaf;

    // dst ports
    // CPU access to registers via APB
    apb_channel< apbAddrSt, apbDataSt > apbReg;


    xpRtNestDecodeChannels(std::string name, std::string srcName) :
    apbReg_uLeaf(("apbReg_uLeaf"+name).c_str(), srcName)
    ,apbReg(("apbReg"+name).c_str(), srcName)
    {};
    void bind( xpRtNestDecodeBase<Config> *a, xpRtNestDecodeInverted<Config> *b)
    {
        a->apbReg_uLeaf( apbReg_uLeaf );
        b->apbReg_uLeaf( apbReg_uLeaf );
        a->apbReg( apbReg );
        b->apbReg( apbReg );
    };
};

// GENERATED_CODE_END
