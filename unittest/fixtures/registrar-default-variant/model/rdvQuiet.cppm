//

// GENERATED_CODE_PARAM --block=rdvQuiet --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "rdvTopVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module rdvTest_rdvQuiet.block;
import rdvTest_rdvQuiet.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
export template<typename Config>
SC_MODULE(rdvQuiet), public blockBase, public rdvQuietBase<Config>
{
private:

public:
    SC_HAS_PROCESS(rdvQuiet);

    // inherited names usable unqualified (no Config:: / this->)
    using rdvQuietBase<Config>::RDV_ALGO;


    rdvQuiet(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~rdvQuiet() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    void report(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
rdvQuiet<Config>::rdvQuiet(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("rdvQuiet", name(), bbMode)
        ,rdvQuietBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(report);
};

// Reports the algorithm this site resolved. The verilated wrapper carries no
// such thread, so the line's absence is what tells the two apart.
template<typename Config>
void rdvQuiet<Config>::report(void)
{
    log_.logPrint(std::format("{} resolved algorithm {}", this->name(),
        (uint64_t)RDV_ALGO), LOG_IMPORTANT);
}

