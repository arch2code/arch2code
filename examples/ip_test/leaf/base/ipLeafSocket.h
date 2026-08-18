#ifndef IPLEAF_SOCKET_H
#define IPLEAF_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipLeaf
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "instanceFactory.h"
import ip_test_ipLeaf.base;
#include "ipLeafVariantConfig.h"

template<typename Config>
SC_MODULE(ipLeafSocket), public blockBase, public ipLeafBase<Config>
{
private:
    struct registerBlock
    {
        registerBlock(const char * variant_)
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("ipLeaf_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<ipLeafSocket<Config>>(blockName, variant, bbMode));}, variant_, "ip_test");
        }
    };
    static registerBlock registerBlock_;
public:
    SC_HAS_PROCESS(ipLeafSocket);

    ipLeafSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ipLeafSocket() override = default;

private:

// GENERATED_CODE_END
};

#endif //IPLEAF_SOCKET_H
