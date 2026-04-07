#ifndef DUT_H
#define DUT_H

//

#include "systemc.h"

// GENERATED_CODE_PARAM --block=dut
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "dutBase.h"
#include "pySocketIncludes.h"

SC_MODULE(dut), public blockBase, public dutBase
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("dut_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<dut>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:

    dut(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~dut() override = default;

    // GENERATED_CODE_END
    // block implementation members
    void dutListener(void);
    void dut2PythonListener(void);
};

#endif //DUT_H
