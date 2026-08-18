#ifndef BLOCKGREGS_SOCKET_H
#define BLOCKGREGS_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockGRegs
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "instanceFactory.h"
import mixed_blockGRegs.base;
#include "mixedVariantConfig.h"

template<typename Config>
SC_MODULE(blockGRegsSocket), public blockBase, public blockGRegsBase<Config>
{
private:
    struct registerBlock
    {
        registerBlock(const char * variant_)
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("blockGRegs_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<blockGRegsSocket<Config>>(blockName, variant, bbMode));}, variant_, "mixed");
        }
    };
    static registerBlock registerBlock_;
public:
    SC_HAS_PROCESS(blockGRegsSocket);

    blockGRegsSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockGRegsSocket() override = default;

private:

// GENERATED_CODE_END
};

#endif //BLOCKGREGS_SOCKET_H
