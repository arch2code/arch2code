//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "ip.h"
template<typename Config>
void ip<Config>::regHandler(void) { //handle register decode
    registerHandler< apbAddrSt, apbDataSt >(regs, this->apbReg, (1<<(9))-1); }

template<typename Config>
ip<Config>::ip(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("ip", name(), bbMode)
        ,ipBase<Config>(name(), variant)
        ,regs(log_)
        ,ipCfg(ipCfgSt<Config>::_packedSt(0x0))
        ,ipLastData()
        ,ipMem(name(), "ipMem", mems, Config::IP_MEM_DEPTH)
        ,ipFixedMem(name(), "ipFixedMem", mems, Config::IP_MEM_DEPTH)
        ,ipNonConstMem(name(), "ipNonConstMem", mems, instanceFactory::getParam("ip", variant, "IP_NONCONST_DEPTH"))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // Generated register/memory address offsets
    constexpr uint64_t REG_ADDR_IP_IPMEM = 0x0;
    constexpr uint64_t REG_ADDR_IP_IPFIXEDMEM = 0x80;
    constexpr uint64_t REG_ADDR_IP_IPNONCONSTMEM = 0x100;
    constexpr uint64_t REG_ADDR_IP_IPCFG = 0x180;
    constexpr uint64_t REG_ADDR_IP_IPLASTDATA = 0x188;

    // register memories for FW access
    regs.addMemory( REG_ADDR_IP_IPMEM, ipMemSt<Config>::_byteWidth, Config::IP_MEM_DEPTH, std::string(this->name()) + ".ipMem", &ipMem);
    regs.addMemory( REG_ADDR_IP_IPFIXEDMEM, ipFixedSt::_byteWidth, Config::IP_MEM_DEPTH, std::string(this->name()) + ".ipFixedMem", &ipFixedMem);
    regs.addMemory( REG_ADDR_IP_IPNONCONSTMEM, ipFixedSt::_byteWidth, instanceFactory::getParam("ip", variant, "IP_NONCONST_DEPTH"), std::string(this->name()) + ".ipNonConstMem", &ipNonConstMem);
    // register registers for FW access
    regs.addRegister( REG_ADDR_IP_IPCFG, 2, "ipCfg", &ipCfg );
    regs.addRegister( REG_ADDR_IP_IPLASTDATA, 1, "ipLastData", &ipLastData );
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
        log_.logPrint(std::format("{} received data 0x{:x}", this->name(), (uint64_t)data.data), LOG_IMPORTANT);
        this->ipDataIf->ack();
    }
}
