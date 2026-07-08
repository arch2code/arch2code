#ifndef SOMERAPPER_H
#define SOMERAPPER_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=someRapper
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
import someRapper.base;
#include "apb_channel.h"
import apbDecode;
using namespace apbDecode_ns;
//contained instances base module imports
import apbDecode.base;
import blockA.base;
import blockB.base;

SC_MODULE(someRapper), public blockBase, public someRapperBase
{
private:

public:
    // channels
    // CPU access to SoC registers in the design
    apb_channel< apbAddrSt, apbDataSt > apbReg_uBlockA;
    // CPU access to SoC registers in the design
    apb_channel< apbAddrSt, apbDataSt > apbReg_uBlockB;

    //instances contained in block
    std::shared_ptr<apbDecodeBase> uAPBDecode;
    std::shared_ptr<blockABase> uBlockA;
    std::shared_ptr<blockBBase> uBlockB;

    someRapper(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~someRapper() override = default;

// GENERATED_CODE_END
};
#endif //SOMERAPPER_H
