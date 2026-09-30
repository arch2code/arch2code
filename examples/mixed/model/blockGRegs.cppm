//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockGRegs --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "apb_channel.h"
#include "status_channel.h"
#include "addressMap.h"
#include "hwRegister.h"
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=moduleExport
export module mixed_blockGRegs.block;
import mixed_blockGRegs.base;
import mixed.blockGRegs.config;
import mixed;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=blockRegs --section=header
using namespace mixed_ns;
export template<typename Config>
SC_MODULE(blockGRegs), public blockBase, public blockGRegsBase<Config>
{
private:
    void regHandler(void);
    addressMap _a2cRegs;

public:

    SC_HAS_PROCESS(blockGRegs);

    blockGRegs(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockGRegs() override = default;

    //registers
    hwRegisterIf< dRegSt, status_out<dRegSt>, 4, false> rwG_reg; // A Read Write register owned by parameterized container blockG and forwarded to a leaf
    
    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=blockRegs --section=init



template<typename Config>
void blockGRegs<Config>::regHandler(void) { //handle register decode
    registerHandler< apbAddrSt, apbDataSt >(_a2cRegs, this->apbReg, (1<<(3))-1);
}

template<typename Config>
blockGRegs<Config>::blockGRegs(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockGRegs", name(), bbMode)
        ,blockGRegsBase<Config>(name(), variant)
        ,_a2cRegs(log_)
        ,rwG_reg(&this->rwG, dRegSt::_packedSt(0x0))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=blockRegs --section=body
{
    // Generated register/memory address offsets
    constexpr uint64_t REG_ADDR_BLOCKG_RWG = 0x0;
    
    // register registers for FW access
    _a2cRegs.addRegister(REG_ADDR_BLOCKG_RWG, 1, "rwG", &rwG_reg );
    SC_THREAD(regHandler);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

