#ifndef IPSTDTOP_SOCKET_H
#define IPSTDTOP_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipStdTop
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "instanceFactory.h"
import ip_ipStdTop.base;

SC_MODULE(ipStdTopSocket), public blockBase, public ipStdTopBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("ipStdTop_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<ipStdTopSocket>(blockName, variant, bbMode));}, "", "ip");
        }
    };
    static registerBlock registerBlock_;
public:

    ipStdTopSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ipStdTopSocket() override = default;

private:

// GENERATED_CODE_END
};

#endif //IPSTDTOP_SOCKET_H
