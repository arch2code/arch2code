// GENERATED_CODE_PARAM --block=cpu
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "cpuSocket.h"

SC_HAS_PROCESS(cpuSocket);

cpuSocket::registerBlock cpuSocket::registerBlock_; //register the block with the factory

void cpuSocket::cpu_mainSocket(void) {
    port_socket(cpu_main, "cpu.cpu_main");
}

cpuSocket::cpuSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("cpu", name(), bbMode)
        ,cpuBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(cpu_mainSocket);

// GENERATED_CODE_END
}
