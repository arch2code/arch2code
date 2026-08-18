#ifndef NESTED_SOCKET_H
#define NESTED_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=nested
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "instanceFactory.h"
import nested.base;

SC_MODULE(nestedSocket), public blockBase, public nestedBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("nested_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<nestedSocket>(blockName, variant, bbMode));}, "", "nested");
        }
    };
    static registerBlock registerBlock_;
public:

    nestedSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~nestedSocket() override = default;

private:

// GENERATED_CODE_END
};

#endif //NESTED_SOCKET_H
