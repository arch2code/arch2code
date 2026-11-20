//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegsScale --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "apb_channel.h"
#include "rdy_vld_channel.h"
#include "addressMap.h"
#include "hwRegister.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module uvmRegs_uvmRegsScale.block;
import uvmRegs_uvmRegsScale.base;
import uvmRegs.uvmRegsScale.config;
import uvmRegs;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace uvmRegs_ns;
export template<typename Config>
SC_MODULE(uvmRegsScale), public blockBase, public uvmRegsScaleBase<Config>
{
private:
    void regHandler(void);
    addressMap _a2cRegs;

public:
    SC_HAS_PROCESS(uvmRegsScale);

    // inherited names usable unqualified (no Config:: / this->)
    using uvmRegsScaleBase<Config>::UVM_REGS_SCALE_W;
    using uvmRegsScaleBase<Config>::out;
    using uvmRegsScaleBase<Config>::in;
    using uvmRegsScaleBase<Config>::apbReg;


    //registers
    hwRegister< uvmRegsScaleSt<Config>, 4 > offset; // Added to each word

    // inherited parameterized types usable unqualified (no <Config>)
    using typename uvmRegsScaleBase<Config>::uvmRegsScaleT;
    using typename uvmRegsScaleBase<Config>::uvmRegsScaleSt;

    uvmRegsScale(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~uvmRegsScale() override = default;

    // GENERATED_CODE_END
    // block implementation members

private:
    void datapath(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
void uvmRegsScale<Config>::regHandler(void) { //handle register decode
    registerHandler< uvmRegsAddrSt, uvmRegsDataSt >(_a2cRegs, this->apbReg, (1<<(3))-1); }

template<typename Config>
uvmRegsScale<Config>::uvmRegsScale(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("uvmRegsScale", name(), bbMode)
        ,uvmRegsScaleBase<Config>(name(), variant)
        ,_a2cRegs(log_)
        ,offset(typename uvmRegsScaleSt::_packedSt(0x1))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // Generated register/memory address offsets
    constexpr uint64_t REG_ADDR_UVMREGSSCALE_OFFSET = 0x0;

    // register registers for FW access
    _a2cRegs.addRegister( REG_ADDR_UVMREGSSCALE_OFFSET, 1, "offset", &offset );
    SC_THREAD(regHandler);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(datapath);
};

template<typename Config>
void uvmRegsScale<Config>::datapath(void)
{
    while (true) {
        uvmRegsWordSt w;
        in->read(w);
        w.word = static_cast<uvmRegsWordT>(w.word + offset.read().offset);
        out->write(w);
    }
}
