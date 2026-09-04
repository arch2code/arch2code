//

// GENERATED_CODE_PARAM --block=vliDrv --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "vliContVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
#include "q_assert.h"
// GENERATED_CODE_BEGIN --template=moduleExport
export module vlInh_vliDrv.block;
import vlInh_vliDrv.base;
import vlInh_vliCont;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace vlInh_vliCont_ns;
export template<typename Config>
SC_MODULE(vliDrv), public blockBase, public vliDrvBase<Config>
{
private:

public:
    SC_HAS_PROCESS(vliDrv);

    // inherited names usable unqualified (no Config:: / this->)
    using vliDrvBase<Config>::VLI_WIDTH;
    using vliDrvBase<Config>::out;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename vliDrvBase<Config>::vliPixelT;
    using typename vliDrvBase<Config>::vliSt;

    vliDrv(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~vliDrv() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    static constexpr uint32_t SAMPLE_COUNT = 4;
    static constexpr uint32_t FIRST_TAG = 0;
    // Top-bit-set stimulus for THIS chain's width. At VLI_WIDTH 10 it is 512,
    // which does not fit the 8-bit variant, so a leaf built at the wrong width
    // truncates it and the checker sees a wrong number rather than nothing.
    static constexpr uint32_t FIRST_DATA = 1u << (Config::VLI_WIDTH - 1);
    static constexpr uint32_t FIRST_MARK = 0x50;
    void drive(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
vliDrv<Config>::vliDrv(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("vliDrv", name(), bbMode)
        ,vliDrvBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(drive);
};

// Drives four samples into this instance's chain. The algo and wid fields are
// left at zero: they are the leaf's to stamp and the checker's to read back.
template<typename Config>
void vliDrv<Config>::drive(void)
{
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        vliSt sample{};
        sample.tag  = FIRST_TAG + i;
        sample.algo = 0;
        sample.wid  = 0;
        sample.data = FIRST_DATA + i;
        sample.mark = FIRST_MARK + i;
        out->push(sample);
    }
}
