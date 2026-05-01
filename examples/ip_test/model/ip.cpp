//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

// GENERATED_CODE_PARAM --block=ip
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "ip.h"
SC_HAS_PROCESS(ip);

ip::registerBlock ip::registerBlock_; //register the block with the factory

void ip::regHandler(void) { //handle register decode
    registerHandler< apbAddrSt, apbDataSt >(regs, apbReg, (1<<(4))-1); }

ip::ip(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("ip", name(), bbMode)
        ,ipBase(name(), variant)
        ,regs(log_)
        ,ipCfg(ipCfgSt::_packedSt(0x0))
        ,ipLastData()
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // register registers for FW access
    regs.addRegister( 0x0, 2, "ipCfg", &ipCfg );
    regs.addRegister( 0x8, 1, "ipLastData", &ipLastData );
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

