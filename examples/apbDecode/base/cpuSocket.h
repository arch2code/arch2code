#ifndef CPU_SOCKET_H
#define CPU_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=cpu
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "apb_port_socket.h"
#include "instanceFactory.h"
import apbDecode_cpu.base;

SC_MODULE(cpuSocket), public blockBase, public cpuBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("cpu_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<cpuSocket>(blockName, variant, bbMode));}, "", "apbDecode");
        }
    };
    static registerBlock registerBlock_;
public:

    cpuSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~cpuSocket() override = default;

private:
    void apbRegSocket(void);

// GENERATED_CODE_END
};

#endif //CPU_SOCKET_H
