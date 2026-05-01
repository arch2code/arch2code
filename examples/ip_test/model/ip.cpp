//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

// GENERATED_CODE_PARAM --block=ip
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "ip.h"
SC_HAS_PROCESS(ip);

ip::registerBlock ip::registerBlock_; //register the block with the factory

void ip::regHandler(void) { //handle register decode
    registerHandler< apbAddrSt, apbDataSt >(regs, apbReg, (1<<(9))-1); }

ip::ip(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("ip", name(), bbMode)
        ,ipBase(name(), variant)
        ,regs(log_)
        ,ipCfg(ipCfgSt::_packedSt(0x0))
        ,ipLastData()
        ,ipMem(name(), "ipMem", mems, IP_MEM_DEPTH)
        ,ipFixedMem(name(), "ipFixedMem", mems, IP_MEM_DEPTH)
        ,ipNonConstMem(name(), "ipNonConstMem", mems, IP_NONCONST_DEPTH)
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
    regs.addMemory( REG_ADDR_IP_IPMEM, ipMemSt::_byteWidth, IP_MEM_DEPTH, std::string(this->name()) + ".ipMem", &ipMem);
    regs.addMemory( REG_ADDR_IP_IPFIXEDMEM, ipFixedSt::_byteWidth, IP_MEM_DEPTH, std::string(this->name()) + ".ipFixedMem", &ipFixedMem);
    regs.addMemory( REG_ADDR_IP_IPNONCONSTMEM, ipFixedSt::_byteWidth, IP_NONCONST_DEPTH, std::string(this->name()) + ".ipNonConstMem", &ipNonConstMem);
    // register registers for FW access
    regs.addRegister( REG_ADDR_IP_IPCFG, 2, "ipCfg", &ipCfg );
    regs.addRegister( REG_ADDR_IP_IPLASTDATA, 1, "ipLastData", &ipLastData );
    SC_THREAD(regHandler);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(dataHandler);
};

void ip::dataHandler(void)
{
    ipDataSt data;
    while (true) {
        ipDataIf->pushReceive(data);
        ipLastData.write(data);
        log_.logPrint(std::format("{} received data 0x{:x}", this->name(), (uint64_t)data.data), LOG_IMPORTANT);
        ipDataIf->ack();
    }
}

