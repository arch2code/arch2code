//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=xpRtNestDecode --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "apb_channel.h"
#include "apbBusDecode.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpRtInh_xpRtNestDecode.block;
import xpRtInh_xpRtNestDecode.base;
import xpRtInh.xpRtNestDecode.config;
import common_shared_types;
import xpRtInh;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace common_shared_types_ns;
using namespace xpRtInh_ns;
export template<typename Config>
SC_MODULE(xpRtNestDecode), public blockBase, public xpRtNestDecodeBase<Config>
{
private:
    void routerDecode(void);
    abpBusDecode< apbAddrSt, apbDataSt > decoder;

public:
    SC_HAS_PROCESS(xpRtNestDecode);

    // inherited names usable unqualified (no Config:: / this->)
    using xpRtNestDecodeBase<Config>::RT_WIDTH;
    using xpRtNestDecodeBase<Config>::apbReg_uLeaf;
    using xpRtNestDecodeBase<Config>::apbReg;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpRtNestDecodeBase<Config>::cfgDataT;
    using typename xpRtNestDecodeBase<Config>::cfgSt;

    xpRtNestDecode(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpRtNestDecode() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
void xpRtNestDecode<Config>::routerDecode(void) //handle apb routing for register
{
    log_.logPrint(std::format("SystemC Thread:{} started", __func__));
    decoder.decodeThread();
}

template<typename Config>
xpRtNestDecode<Config>::xpRtNestDecode(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpRtNestDecode", name(), bbMode)
        ,xpRtNestDecodeBase<Config>(name(), variant)
        ,decoder(16, 20, apbReg, {
            &apbReg_uLeaf})
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    SC_THREAD(routerDecode);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

