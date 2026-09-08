//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "apb_channel.h"
#include "push_ack_channel.h"
#include "addressMap.h"
#include "hwRegister.h"
#include "hwMemory.h"
// GENERATED_CODE_END
// user #includes here
#include "q_assert.h"

// GENERATED_CODE_BEGIN --template=moduleExport
export module ip.block;
import ip.base;
import ip.ip.config;
import ip;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace ip_ns;
export template<typename Config>
SC_MODULE(ip), public blockBase, public ipBase<Config>
{
private:
    void regHandler(void);
    addressMap _a2cRegs;

public:
    SC_HAS_PROCESS(ip);

    // inherited names usable unqualified (no Config:: / this->)
    using ipBase<Config>::IP_DATA_WIDTH;
    using ipBase<Config>::IP_MEM_DEPTH;
    using ipBase<Config>::IP_NONCONST_DEPTH;
    using ipBase<Config>::ipDataIf;
    using ipBase<Config>::regs;


    //registers
    hwRegister< ipCfgSt<Config>, 20 > ipCfg; // IP configuration
    hwRegister< ipDataSt<Config>, 20 > ipLastData; // Last data word received on ipDataIf

    memories mems;
    //memories
    hwMemory< ipMemSt<Config> > ipMem;
    hwMemory< ipFixedSt > ipFixedMem;
    hwMemory< ipFixedSt > ipNonConstMem;
    hwMemory< ipMemSt<Config> > ipDerivedDepthMem;

    // inherited parameterized types usable unqualified (no <Config>)
    using ipBase<Config>::IP_DATA_WIDTH_X2;
    using ipBase<Config>::IP_DATA_WIDTH_X4;
    using ipBase<Config>::IP_MEM_DEPTH_X2;
    using ipBase<Config>::IP_MEM_DEPTH_X4;
    using typename ipBase<Config>::ipDataT;
    using typename ipBase<Config>::ipMemAddrT;
    using typename ipBase<Config>::ipDerivedWidthT;
    using typename ipBase<Config>::ipDerivedMemAddrT;
    using typename ipBase<Config>::ipDataSt;
    using typename ipBase<Config>::ipCfgSt;
    using typename ipBase<Config>::ipMemSt;
    using typename ipBase<Config>::ipMemAddrSt;
    using typename ipBase<Config>::ipBurstSt;
    using typename ipBase<Config>::ipDerivedMemAddrSt;
    using typename ipBase<Config>::ipParamNestedSt;

    ip(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ip() override = default;
    void setTimed(int nsec, timedDelayMode mode) override
    {
        ipBase<Config>::setTimed(nsec, mode);
        mems.setTimed(nsec, mode);
    }

    // GENERATED_CODE_END
    // block implementation members
private:
    void dataHandler(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
void ip<Config>::regHandler(void) { //handle register decode
    registerHandler< ipRegAddrSt, ipRegDataSt >(_a2cRegs, this->regs, (1<<(10))-1); }

template<typename Config>
ip<Config>::ip(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("ip", name(), bbMode)
        ,ipBase<Config>(name(), variant)
        ,_a2cRegs(log_)
        ,ipCfg(typename ipCfgSt::_packedSt(0x0))
        ,ipLastData()
        ,ipMem(name(), "ipMem", mems, Config::IP_MEM_DEPTH)
        ,ipFixedMem(name(), "ipFixedMem", mems, Config::IP_MEM_DEPTH)
        ,ipNonConstMem(name(), "ipNonConstMem", mems, Config::IP_NONCONST_DEPTH)
        ,ipDerivedDepthMem(name(), "ipDerivedDepthMem", mems, ((Config::IP_MEM_DEPTH * 2) * 2))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // Generated register/memory address offsets
    constexpr uint64_t REG_ADDR_IP_IPMEM = 0x0;
    constexpr uint64_t REG_ADDR_IP_IPFIXEDMEM = 0x200;
    constexpr uint64_t REG_ADDR_IP_IPNONCONSTMEM = 0x280;
    constexpr uint64_t REG_ADDR_IP_IPCFG = 0x300;
    constexpr uint64_t REG_ADDR_IP_IPLASTDATA = 0x318;

    // register memories for FW access
    _a2cRegs.addMemory( REG_ADDR_IP_IPMEM, ipMemSt::_byteWidth, Config::IP_MEM_DEPTH, std::string(this->name()) + ".ipMem", &ipMem);
    _a2cRegs.addMemory( REG_ADDR_IP_IPFIXEDMEM, ipFixedSt::_byteWidth, Config::IP_MEM_DEPTH, std::string(this->name()) + ".ipFixedMem", &ipFixedMem);
    _a2cRegs.addMemory( REG_ADDR_IP_IPNONCONSTMEM, ipFixedSt::_byteWidth, Config::IP_NONCONST_DEPTH, std::string(this->name()) + ".ipNonConstMem", &ipNonConstMem);
    // register registers for FW access
    _a2cRegs.addRegister( REG_ADDR_IP_IPCFG, 10, "ipCfg", &ipCfg );
    _a2cRegs.addRegister( REG_ADDR_IP_IPLASTDATA, 9, "ipLastData", &ipLastData );
    SC_THREAD(regHandler);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(dataHandler);
};

template<typename Config>
void ip<Config>::dataHandler(void)
{
    ipDataSt data;
    while (true) {
        ipDataIf->pushReceive(data);
        ipLastData.write(data);
        log_.logPrint(std::format("{} received data 0x{:x}{:016x} marker {}", this->name(), data.data.word[1], data.data.word[0], (uint64_t)data.marker), LOG_IMPORTANT);
        Q_ASSERT(data.marker == 1, "ipDataIf marker bit was not preserved through the thunker");
        if constexpr (IP_DATA_WIDTH > 64) {
            Q_ASSERT(data.data.word[1] == 0x2A, "ipDataIf high data word was not preserved through the thunker");
        }
        ipDataIf->ack();
    }
}
