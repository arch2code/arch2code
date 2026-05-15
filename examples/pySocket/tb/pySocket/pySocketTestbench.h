#ifndef PYSOCKET_TANDEM_H
#define PYSOCKET_TANDEM_H
// 

// GENERATED_CODE_PARAM --block=pySocket
// GENERATED_CODE_BEGIN --template=testbench --section=header
#include "systemc.h"
#include "instanceFactory.h"

#include "pySocketBase.h"
#include "pySocketExternal.h"

class pySocketTestbench: public sc_module, public blockBase, public pySocketChannels {

    private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("pySocketTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<pySocketTestbench>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;

public:

    std::shared_ptr<pySocketBase> pySocket;
    pySocketExternal external;

    pySocketTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~pySocketTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END

#endif /* PYSOCKET_TANDEM_H */
