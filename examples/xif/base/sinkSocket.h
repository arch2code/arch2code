#ifndef SINK_SOCKET_H
#define SINK_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=sink
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "push_ack_port_socket.h"
#include "instanceFactory.h"
import xif_sink.base;
#include "xifVariantConfig.h"

template<typename Config>
SC_MODULE(sinkSocket), public blockBase, public sinkBase<Config>
{
private:
    struct registerBlock
    {
        registerBlock(const char * variant_)
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("sink_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<sinkSocket<Config>>(blockName, variant, bbMode));}, variant_, "xif");
        }
    };
    static registerBlock registerBlock_;
public:
    SC_HAS_PROCESS(sinkSocket);

    sinkSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~sinkSocket() override = default;

private:
    void inSocket(void);

// GENERATED_CODE_END
};

#endif //SINK_SOCKET_H
