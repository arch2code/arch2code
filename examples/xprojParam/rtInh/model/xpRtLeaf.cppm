//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=xpRtLeaf --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "apb_channel.h"
#include "addressMap.h"
#include "hwRegister.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpRtInh_xpRtLeaf.block;
import xpRtInh_xpRtLeaf.base;
import xpRtInh.xpRtLeaf.config;
import xpRtInh;
import common_shared_types;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpRtInh_ns;
using namespace common_shared_types_ns;
export template<typename Config>
SC_MODULE(xpRtLeaf), public blockBase, public xpRtLeafBase<Config>
{
private:
    void regHandler(void);
    addressMap _a2cRegs;

public:
    SC_HAS_PROCESS(xpRtLeaf);

    // inherited names usable unqualified (no Config:: / this->)
    using xpRtLeafBase<Config>::RT_WIDTH;
    using xpRtLeafBase<Config>::apbReg;


    //registers
    hwRegister< cfgSt<Config>, 4 > cfg; // xpRtLeaf configuration register

    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpRtLeafBase<Config>::cfgDataT;
    using typename xpRtLeafBase<Config>::cfgSt;

    xpRtLeaf(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpRtLeaf() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
void xpRtLeaf<Config>::regHandler(void) { //handle register decode
    registerHandler< apbAddrSt, apbDataSt >(_a2cRegs, this->apbReg, (1<<(3))-1); }

template<typename Config>
xpRtLeaf<Config>::xpRtLeaf(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpRtLeaf", name(), bbMode)
        ,xpRtLeafBase<Config>(name(), variant)
        ,_a2cRegs(log_)
        ,cfg(typename cfgSt::_packedSt(0x0))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // Generated register/memory address offsets
    constexpr uint64_t REG_ADDR_XPRTLEAF_CFG = 0x0;

    // register registers for FW access
    _a2cRegs.addRegister( REG_ADDR_XPRTLEAF_CFG, 1, "cfg", &cfg );
    SC_THREAD(regHandler);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

