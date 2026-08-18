#ifndef SOMERAPPER_SOCKET_H
#define SOMERAPPER_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=someRapper
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "instanceFactory.h"
import apbDecode_someRapper.base;

SC_MODULE(someRapperSocket), public blockBase, public someRapperBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("someRapper_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<someRapperSocket>(blockName, variant, bbMode));}, "", "apbDecode");
        }
    };
    static registerBlock registerBlock_;
public:

    someRapperSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~someRapperSocket() override = default;

private:

// GENERATED_CODE_END
};

#endif //SOMERAPPER_SOCKET_H
