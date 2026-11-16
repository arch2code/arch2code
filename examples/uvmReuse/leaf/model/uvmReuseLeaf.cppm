//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseLeaf --mode=module
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
export module uvmReuseLeaf.block;
import uvmReuseLeaf.base;
import uvmReuseLeaf.config;
import uvmReuseLeaf;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace uvmReuseLeaf_ns;
export template<typename Config>
SC_MODULE(uvmReuseLeaf), public blockBase, public uvmReuseLeafBase<Config>
{
private:
    void regHandler(void);
    addressMap _a2cRegs;

public:
    SC_HAS_PROCESS(uvmReuseLeaf);

    // inherited names usable unqualified (no Config:: / this->)
    using uvmReuseLeafBase<Config>::UVM_REUSE_OFF_W;
    using uvmReuseLeafBase<Config>::in;
    using uvmReuseLeafBase<Config>::out;
    using uvmReuseLeafBase<Config>::apbReg;


    //registers
    hwRegister< uvmReuseOffSt<Config>, 4 > offset; // Added to each pixel

    // inherited parameterized types usable unqualified (no <Config>)
    using typename uvmReuseLeafBase<Config>::uvmReuseOffT;
    using typename uvmReuseLeafBase<Config>::uvmReuseOffSt;

    uvmReuseLeaf(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~uvmReuseLeaf() override = default;

    // GENERATED_CODE_END
    // block implementation members

private:
    // One beat between the input and the output thread. The RTL's path from
    // in to out is combinational, so the model must take the next input
    // while the output still waits on the last.
    sc_fifo<uvmReuseBeatSt> beats;
    void accept(void);
    void datapath(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
void uvmReuseLeaf<Config>::regHandler(void) { //handle register decode
    registerHandler< uvmReuseAddrSt, uvmReuseDataSt >(_a2cRegs, this->apbReg, (1<<(3))-1); }

template<typename Config>
uvmReuseLeaf<Config>::uvmReuseLeaf(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("uvmReuseLeaf", name(), bbMode)
        ,uvmReuseLeafBase<Config>(name(), variant)
        ,_a2cRegs(log_)
        ,offset(typename uvmReuseOffSt::_packedSt(0x1))
// GENERATED_CODE_END
        ,beats("beats", 1)
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // Generated register/memory address offsets
    constexpr uint64_t REG_ADDR_UVMREUSELEAF_OFFSET = 0x0;

    // register registers for FW access
    _a2cRegs.addRegister( REG_ADDR_UVMREUSELEAF_OFFSET, 1, "offset", &offset );
    SC_THREAD(regHandler);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(accept);
    SC_THREAD(datapath);
};

template<typename Config>
void uvmReuseLeaf<Config>::accept(void)
{
    while (true) {
        uvmReuseBeatSt b;
        in->read(b);
        beats.write(b);
    }
}

template<typename Config>
void uvmReuseLeaf<Config>::datapath(void)
{
    while (true) {
        uvmReuseBeatSt b = beats.read();
        b.pixel = static_cast<uvmReusePixelT>(b.pixel + offset.read().offset);
        out->write(b);
    }
}
