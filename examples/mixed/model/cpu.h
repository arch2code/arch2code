#ifndef CPU_H
#define CPU_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=cpu
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "cpuBase.h"
#include "mixedIncludes.h"

SC_MODULE(cpu), public blockBase, public cpuBase
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("cpu_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<cpu>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:

    cpu(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~cpu() override = default;

    // GENERATED_CODE_END

    // block implementation members
private:
    void fwTest(void);
    void test_mem_37bit_cpu_rw(void);
   
};

#endif //CPU_H
