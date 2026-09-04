//

// GENERATED_CODE_PARAM --block=xpCppWrap --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "push_ack_port_thunker.h"
#include "xpCppWrapVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpCppAxis_xpCppWrap.block;
import xpCppAxis_xpCppWrap.base;
import xpCppAxis_xpCppWrap;
import xpCppLeaf;
import xpCppLeaf_xpCppLeafEq.base;
import xpCppLeaf_xpCppLeafOrder.base;
import xpCppLeaf_xpCppLeafSign.base;
import xpCppLeaf_xpCppLeafNest.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpCppAxis_xpCppWrap_ns;
using namespace xpCppLeaf_ns;
export template<typename Config>
SC_MODULE(xpCppWrap), public blockBase, public xpCppWrapBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpCppWrap);

    // inherited names usable unqualified (no Config:: / this->)
    using xpCppWrapBase<Config>::WRAP_PIXEL_WIDTH;
    using xpCppWrapBase<Config>::eqIn;
    using xpCppWrapBase<Config>::orderIn;
    using xpCppWrapBase<Config>::signIn;
    using xpCppWrapBase<Config>::nestIn;

    //instances contained in block
    std::shared_ptr<xpCppLeafEqBase<xpCppLeafEqV0Config>> uLeafEq;
    std::shared_ptr<xpCppLeafOrderBase<xpCppLeafOrderV0Config>> uLeafOrder;
    std::shared_ptr<xpCppLeafSignBase<xpCppLeafSignV0Config>> uLeafSign;
    std::shared_ptr<xpCppLeafNestBase<xpCppLeafNestV0Config>> uLeafNest;

    // cross-interface thunkers
    push_ack_port_thunker<wrapEqSt<Config>, leafEqSt<xpCppLeafEqV0Config>, true> thunker_uLeafEq;
    push_ack_port_thunker<wrapOrderSt<Config>, leafOrderSt<xpCppLeafOrderV0Config>, false> thunker_uLeafOrder;
    push_ack_port_thunker<wrapSignSt<Config>, leafSignSt<xpCppLeafSignV0Config>, false> thunker_uLeafSign;
    push_ack_port_thunker<wrapNestSt<Config>, leafNestSt<xpCppLeafNestV0Config>, false> thunker_uLeafNest;

    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpCppWrapBase<Config>::wrapPixelT;
    using typename xpCppWrapBase<Config>::wrapEqSt;
    using typename xpCppWrapBase<Config>::wrapOrderSt;
    using typename xpCppWrapBase<Config>::wrapSignSt;
    using typename xpCppWrapBase<Config>::wrapNestSt;

    xpCppWrap(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpCppWrap() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpCppWrap<Config>::xpCppWrap(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpCppWrap", name(), bbMode)
        ,xpCppWrapBase<Config>(name(), variant)
        ,uLeafEq(std::dynamic_pointer_cast<xpCppLeafEqBase<xpCppLeafEqV0Config>>(instanceFactory::createInstance(name(), "uLeafEq", "xpCppLeafEq", "v0", "xpCppAxis.xpCppAxis_xpCppWrap.xpCppLeaf_xpCppLeafEq")))
        ,uLeafOrder(std::dynamic_pointer_cast<xpCppLeafOrderBase<xpCppLeafOrderV0Config>>(instanceFactory::createInstance(name(), "uLeafOrder", "xpCppLeafOrder", "v0", "xpCppAxis.xpCppAxis_xpCppWrap.xpCppLeaf_xpCppLeafOrder")))
        ,uLeafSign(std::dynamic_pointer_cast<xpCppLeafSignBase<xpCppLeafSignV0Config>>(instanceFactory::createInstance(name(), "uLeafSign", "xpCppLeafSign", "v0", "xpCppAxis.xpCppAxis_xpCppWrap.xpCppLeaf_xpCppLeafSign")))
        ,uLeafNest(std::dynamic_pointer_cast<xpCppLeafNestBase<xpCppLeafNestV0Config>>(instanceFactory::createInstance(name(), "uLeafNest", "xpCppLeafNest", "v0", "xpCppAxis.xpCppAxis_xpCppWrap.xpCppLeaf_xpCppLeafNest")))
        ,thunker_uLeafEq("thunker_uLeafEq", this->eqIn, uLeafEq->eqIn, name())
        ,thunker_uLeafOrder("thunker_uLeafOrder", this->orderIn, uLeafOrder->orderIn, name())
        ,thunker_uLeafSign("thunker_uLeafSign", this->signIn, uLeafSign->signIn, name())
        ,thunker_uLeafNest("thunker_uLeafNest", this->nestIn, uLeafNest->nestIn, name())
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

