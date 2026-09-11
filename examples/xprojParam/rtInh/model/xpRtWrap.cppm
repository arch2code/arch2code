//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=xpRtWrap --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "apb_channel.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpRtInh_xpRtWrap.block;
import xpRtInh_xpRtWrap.base;
import xpRtInh.xpRtWrap.config;
import xpRtInh_xpRtLeaf.block;
import xpRtInh_xpRtNestDecode.block;
import common_shared_types;
import xpRtInh_xpRtNestDecode.base;
import xpRtInh_xpRtLeaf.base;
import xpRtInh;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace common_shared_types_ns;
using namespace xpRtInh_ns;
export template<typename Config>
SC_MODULE(xpRtWrap), public blockBase, public xpRtWrapBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpRtWrap);

    // inherited names usable unqualified (no Config:: / this->)
    using xpRtWrapBase<Config>::RT_WIDTH;
    using xpRtWrapBase<Config>::apbReg;

    // channels
    // CPU access to registers via APB
    apb_channel< apbAddrSt, apbDataSt > apbReg_uLeaf;

    //instances contained in block
    std::shared_ptr<xpRtNestDecodeBase<Config>> uNestDecode;
    std::shared_ptr<xpRtLeafBase<Config>> uLeaf;

    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpRtWrapBase<Config>::cfgDataT;
    using typename xpRtWrapBase<Config>::cfgSt;

    xpRtWrap(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpRtWrap() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpRtWrap<Config>::xpRtWrap(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpRtWrap", name(), bbMode)
        ,xpRtWrapBase<Config>(name(), variant)
        ,apbReg_uLeaf("xpRtLeaf_apbReg_uLeaf", "xpRtNestDecode")
        ,uNestDecode(std::dynamic_pointer_cast<xpRtNestDecodeBase<Config>>(instanceFactory::createInstance<xpRtNestDecode<Config>>(name(), "uNestDecode", "xpRtNestDecode", variant, "xpRtInh.xpRtInh_xpRtWrap.xpRtInh_xpRtNestDecode")))
        ,uLeaf(std::dynamic_pointer_cast<xpRtLeafBase<Config>>(instanceFactory::createInstance<xpRtLeaf<Config>>(name(), "uLeaf", "xpRtLeaf", variant, "xpRtInh.xpRtInh_xpRtWrap.xpRtInh_xpRtLeaf")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uNestDecode->apbReg(this->apbReg);
    // instance to instance connections via channel
    uNestDecode->apbReg_uLeaf(apbReg_uLeaf);
    uLeaf->apbReg(apbReg_uLeaf);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

