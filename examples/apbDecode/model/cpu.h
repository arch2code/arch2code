#ifndef CPU_H
#define CPU_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=cpu
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
import cpu.base;
#include "apb_channel.h"
import apbDecode;
using namespace apbDecode_ns;

SC_MODULE(cpu), public blockBase, public cpuBase
{
private:

public:

    cpu(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~cpu() override = default;

    // GENERATED_CODE_END
    // block implementation members
    void registerTest(void);
    void endOfTestThread(void);
    void memAccessTest(void);

    void writeBlockATable0Mem(const int, aMemSt &);
    void readBlockATable0Mem(const int, aMemSt &);
    void writeBlockATable1Mem(const int, aMemSt &);
    void readBlockATable1Mem(const int, aMemSt &);
    void writeBlockBTableMem(const int, bMemSt &);
    void readBlockBTableMem(const int, bMemSt &);

};

#endif //CPU_H
