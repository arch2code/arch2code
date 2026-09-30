//

// GENERATED_CODE_PARAM --block=xviDrv --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "xviLeafVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xviMid_xviDrv.block;
import xviMid_xviDrv.base;
import xviLeaf;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xviLeaf_ns;
export template<typename Config>
SC_MODULE(xviDrv), public blockBase, public xviDrvBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xviDrv);

    // inherited names usable unqualified (no Config:: / this->)
    using xviDrvBase<Config>::XVI_WIDTH;
    using xviDrvBase<Config>::out;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename xviDrvBase<Config>::xviPixelT;
    using typename xviDrvBase<Config>::xviSt;

    xviDrv(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xviDrv() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    // Tags run 1..XVI_TAG_COUNT; each sample's payload starts equal to its tag.
    static constexpr unsigned XVI_TAG_COUNT = 4;

    void drive(void);

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xviDrv<Config>::xviDrv(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xviDrv", name(), bbMode)
        ,xviDrvBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(drive);
};

template<typename Config>
void xviDrv<Config>::drive(void)
{
    for (unsigned tag = 1; tag <= XVI_TAG_COUNT; tag++) {
        xviSt sample;
        sample.tag = (xviTagT)tag;
        sample.data = (xviPixelT)tag;
        out->push(sample);
    }
}
