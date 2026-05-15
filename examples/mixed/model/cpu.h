#ifndef CPU_H
#define CPU_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=cpu
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "cpuBase.h"

SC_MODULE(cpu), public blockBase, public cpuBase
{
private:

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
