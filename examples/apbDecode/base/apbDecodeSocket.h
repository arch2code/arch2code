#ifndef APBDECODE_SOCKET_H
#define APBDECODE_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=apbDecode
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "apb_port_socket.h"
#include "instanceFactory.h"
import apbDecode.base;

SC_MODULE(apbDecodeSocket), public blockBase, public apbDecodeBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("apbDecode_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<apbDecodeSocket>(blockName, variant, bbMode));}, "", "apbDecode");
        }
    };
    static registerBlock registerBlock_;
public:

    apbDecodeSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~apbDecodeSocket() override = default;

private:
    void apbReg_uBlockASocket(void);
    void apbReg_uBlockBSocket(void);

// GENERATED_CODE_END
};

#endif //APBDECODE_SOCKET_H
