//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "ip.h"
// === Block factory registration (ip) ===
namespace {
[[maybe_unused]] int _ip_registered = []() -> int {
    instanceFactory::registerBlock("ip_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ip<ipVariant0Config>>(blockName, variant, bbMode)); }, "variant0");
    instanceFactory::registerBlock("ip_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ip<ipVariant1Config>>(blockName, variant, bbMode)); }, "variant1");
    return 0;
}();
} // namespace
// === End block factory registration ===

template<typename Config>
void ip<Config>::regHandler(void) { //handle register decode
    registerHandler< apbAddrSt, apbDataSt >(regs, this->apbReg, (1<<(10))-1); }

template<typename Config>
ip<Config>::ip(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("ip", name(), bbMode)
        ,ipBase<Config>(name(), variant)
        ,regs(log_)
        ,ipCfg(typename ipCfgSt<Config>::_packedSt(0x0))
        ,ipLastData()
        ,ipMem(name(), "ipMem", mems, Config::IP_MEM_DEPTH)
        ,ipFixedMem(name(), "ipFixedMem", mems, Config::IP_MEM_DEPTH)
        ,ipNonConstMem(name(), "ipNonConstMem", mems, Config::IP_NONCONST_DEPTH)
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
    regs.addMemory( REG_ADDR_IP_IPMEM, ipMemSt<Config>::_byteWidth, Config::IP_MEM_DEPTH, std::string(this->name()) + ".ipMem", &ipMem);
    regs.addMemory( REG_ADDR_IP_IPFIXEDMEM, ipFixedSt::_byteWidth, Config::IP_MEM_DEPTH, std::string(this->name()) + ".ipFixedMem", &ipFixedMem);
    regs.addMemory( REG_ADDR_IP_IPNONCONSTMEM, ipFixedSt::_byteWidth, Config::IP_NONCONST_DEPTH, std::string(this->name()) + ".ipNonConstMem", &ipNonConstMem);
    // register registers for FW access
    regs.addRegister( REG_ADDR_IP_IPCFG, 10, "ipCfg", &ipCfg );
    regs.addRegister( REG_ADDR_IP_IPLASTDATA, 9, "ipLastData", &ipLastData );
    SC_THREAD(regHandler);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(dataHandler);
};

template<typename Config>
void ip<Config>::dataHandler(void)
{
    ipDataSt<Config> data;
    while (true) {
        this->ipDataIf->pushReceive(data);
        ipLastData.write(data);
        log_.logPrint(std::format("{} received data 0x{:x}{:016x} marker {}", this->name(), data.data.word[1], data.data.word[0], (uint64_t)data.marker), LOG_IMPORTANT);
        Q_ASSERT(data.marker == 1, "ipDataIf marker bit was not preserved through the thunker");
        if constexpr (Config::IP_DATA_WIDTH > 64) {
            Q_ASSERT(data.data.word[1] == 0x2A, "ipDataIf high data word was not preserved through the thunker");
        }
        this->ipDataIf->ack();
    }
}
