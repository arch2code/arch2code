#ifndef BLOCKF_SOCKET_H
#define BLOCKF_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockF
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "rdy_vld_port_socket.h"
#include "status_port_socket.h"
#include "instanceFactory.h"
import mixed_blockF.base;
#include "mixedVariantConfig.h"

template<typename Config>
SC_MODULE(blockFSocket), public blockBase, public blockFBase<Config>
{
private:
    struct registerBlock
    {
        registerBlock(const char * variant_)
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("blockF_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<blockFSocket<Config>>(blockName, variant, bbMode));}, variant_, "mixed");
        }
    };
    static registerBlock registerBlock_;
public:
    SC_HAS_PROCESS(blockFSocket);

    blockFSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockFSocket() override = default;

private:
    void cStuffIfSocket(void);
    void dStuffIfSocket(void);
    void dSinSocket(void);
    void dSoutSocket(void);
    void rwDObserve(void);

// GENERATED_CODE_END
};

#endif //BLOCKF_SOCKET_H
