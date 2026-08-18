#ifndef SIMPLE_SOCKET_H
#define SIMPLE_SOCKET_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=simple
// GENERATED_CODE_BEGIN --template=socket --section=socket
#include "logging.h"
#include "instanceFactory.h"
import simple.base;

SC_MODULE(simpleSocket), public blockBase, public simpleBase
{
private:
    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("simple_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<simpleSocket>(blockName, variant, bbMode));}, "", "simple");
        }
    };
    static registerBlock registerBlock_;
public:

    simpleSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~simpleSocket() override = default;

private:

// GENERATED_CODE_END
};

#endif //SIMPLE_SOCKET_H
