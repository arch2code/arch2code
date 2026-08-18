#ifndef MIXED_SOCKET_H
#define MIXED_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=mixed
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "instanceFactory.h"
import mixed.base;

SC_MODULE(mixedSocket), public blockBase, public mixedBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("mixed_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<mixedSocket>(blockName, variant, bbMode));}, "", "mixed");
        }
    };
    static registerBlock registerBlock_;
public:

    mixedSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~mixedSocket() override = default;

private:

// GENERATED_CODE_END
};

#endif //MIXED_SOCKET_H
