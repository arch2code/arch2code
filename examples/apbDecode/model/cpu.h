#ifndef CPU_H
#define CPU_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=cpu
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "cpu_base.h"
#include "apbDecodeIncludes.h"

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

    // channels


    cpu(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~cpu() override = default;

    // GENERATED_CODE_END
    // block implementation members
    void registerTest(void);
    void memAccessTest(void);

    void writeBlockATable0Mem(const int, aMemSt &);
    void readBlockATable0Mem(const int, aMemSt &);
    void writeBlockATable1Mem(const int, aMemSt &);
    void readBlockATable1Mem(const int, aMemSt &);
    void writeBlockBTableMem(const int, bMemSt &);
    void readBlockBTableMem(const int, bMemSt &);

};

#endif //CPU_H
