//

// GENERATED_CODE_PARAM --block=xpInhDrv --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
#include "q_assert.h"
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpInhVar_xpInhDrv.block;
import xpInhVar_xpInhDrv.base;
import xpInhVar.xpInhDrv.config;
import xpInhVar_xpInhCont;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpInhVar_xpInhCont_ns;
export template<typename Config>
SC_MODULE(xpInhDrv), public blockBase, public xpInhDrvBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpInhDrv);

    // inherited names usable unqualified (no Config:: / this->)
    using xpInhDrvBase<Config>::INH_WIDTH;
    using xpInhDrvBase<Config>::out;
    using xpInhDrvBase<Config>::out2;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpInhDrvBase<Config>::inhPixelT;
    using typename xpInhDrvBase<Config>::inhSt;

    xpInhDrv(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpInhDrv() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    static constexpr uint32_t SAMPLE_COUNT = 4;
    static constexpr uint32_t FIRST_TAG = 0;
    static constexpr uint32_t FIRST_DATA = 0x31;
    static constexpr uint32_t FIRST_MARK = 0x50;
    void drive(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpInhDrv<Config>::xpInhDrv(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpInhDrv", name(), bbMode)
        ,xpInhDrvBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(drive);
};

// Drives four samples into both chains. The algo field is left at zero: it is
// the leaf's to stamp and the checker's to read back.
template<typename Config>
void xpInhDrv<Config>::drive(void)
{
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        inhSt sample{};
        sample.tag  = FIRST_TAG + i;
        sample.algo = 0;
        sample.data = FIRST_DATA + i;
        sample.mark = FIRST_MARK + i;
        out->push(sample);
        out2->push(sample);
    }
}

