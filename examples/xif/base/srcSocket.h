#ifndef SRC_SOCKET_H
#define SRC_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=src
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "push_ack_port_socket.h"
#include "instanceFactory.h"
import xif_src.base;
#include "xifVariantConfig.h"

template<typename Config>
SC_MODULE(srcSocket), public blockBase, public srcBase<Config>
{
private:
    struct registerBlock
    {
        registerBlock(const char * variant_)
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("src_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<srcSocket<Config>>(blockName, variant, bbMode));}, variant_, "xif");
        }
    };
    static registerBlock registerBlock_;
public:
    SC_HAS_PROCESS(srcSocket);

    srcSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~srcSocket() override = default;

private:
    void outSocket(void);

// GENERATED_CODE_END
};

#endif //SRC_SOCKET_H
