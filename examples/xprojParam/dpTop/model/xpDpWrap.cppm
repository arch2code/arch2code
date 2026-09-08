//

// GENERATED_CODE_PARAM --block=xpDpWrap --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "push_ack_port_thunker.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpDpTop_xpDpWrap.block;
import xpDpTop_xpDpWrap.base;
import xpDpTop.xpDpWrap.config;
import xpDpTop.xpDpChk.config;
import xpDpTop.xpDpLeaf.config;
import xpDpTop.xpDpMid.config;
import xpDpTop.xpDpSrc.config;
import xpDpLeaf.block;
import xpDpMid.block;
import xpDpLeaf;
import xpDpTop_xpDpSrc.base;
import xpDpMid.base;
import xpDpTop_xpDpChk.base;
import xpDpLeaf.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpDpLeaf_ns;
export template<typename Config>
SC_MODULE(xpDpWrap), public blockBase, public xpDpWrapBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpDpWrap);

    // inherited names usable unqualified (no Config:: / this->)
    using xpDpWrapBase<Config>::CUST_ALGO;
    using xpDpWrapBase<Config>::DP_WIDTH;

    // channels
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< dpSt<xpDpTop_xpDpMidCustomerConfig<Config>> > out_0;
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< dpSt<xpDpTop_xpDpChkCustomerConfig> > midOut_0;
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< dpSt<xpDpTop_xpDpLeafLeafXConfig<Config>> > out2;
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< dpSt<xpDpTop_xpDpChkLeafXConfig> > out_1;
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< dpSt<xpDpTop_xpDpMidCustomer2Config> > out4;
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< dpSt<xpDpTop_xpDpChkCustomer2Config> > midOut_1;
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< dpSt<xpDpTop_xpDpMidCustomer3Config> > out3;
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< dpSt<xpDpTop_xpDpChkCustomer3Config> > midOut_2;

    //instances contained in block
    std::shared_ptr<xpDpSrcBase<xpDpTop_xpDpSrcCustomerConfig>> uSrc;
    std::shared_ptr<xpDpMidBase<xpDpTop_xpDpMidCustomerConfig<Config>>> uMid;
    std::shared_ptr<xpDpChkBase<xpDpTop_xpDpChkCustomerConfig>> uChk;
    std::shared_ptr<xpDpMidBase<xpDpTop_xpDpMidCustomer2Config>> uMid2;
    std::shared_ptr<xpDpLeafBase<xpDpTop_xpDpLeafLeafXConfig<Config>>> uLeafX;
    std::shared_ptr<xpDpChkBase<xpDpTop_xpDpChkLeafXConfig>> uChkX;
    std::shared_ptr<xpDpChkBase<xpDpTop_xpDpChkCustomer2Config>> uChk2;
    std::shared_ptr<xpDpMidBase<xpDpTop_xpDpMidCustomer3Config>> uMid3;
    std::shared_ptr<xpDpChkBase<xpDpTop_xpDpChkCustomer3Config>> uChk3;

    // cross-interface thunkers
    push_ack_port_thunker<dpSt<xpDpTop_xpDpMidCustomerConfig<Config>>, dpSt<xpDpTop_xpDpSrcCustomerConfig>, true> thunker_out_0_uSrc;
    push_ack_port_thunker<dpSt<xpDpTop_xpDpChkCustomerConfig>, dpSt<xpDpTop_xpDpMidCustomerConfig<Config>>, true> thunker_midOut_0_uMid;
    push_ack_port_thunker<dpSt<xpDpTop_xpDpLeafLeafXConfig<Config>>, dpSt<xpDpTop_xpDpSrcCustomerConfig>, true> thunker_out2_uSrc;
    push_ack_port_thunker<dpSt<xpDpTop_xpDpChkLeafXConfig>, dpSt<xpDpTop_xpDpLeafLeafXConfig<Config>>, true> thunker_out_1_uLeafX;
    push_ack_port_thunker<dpSt<xpDpTop_xpDpMidCustomer2Config>, dpSt<xpDpTop_xpDpSrcCustomerConfig>, true> thunker_out4_uSrc;
    push_ack_port_thunker<dpSt<xpDpTop_xpDpChkCustomer2Config>, dpSt<xpDpTop_xpDpMidCustomer2Config>, true> thunker_midOut_1_uMid2;
    push_ack_port_thunker<dpSt<xpDpTop_xpDpMidCustomer3Config>, dpSt<xpDpTop_xpDpSrcCustomerConfig>, true> thunker_out3_uSrc;
    push_ack_port_thunker<dpSt<xpDpTop_xpDpChkCustomer3Config>, dpSt<xpDpTop_xpDpMidCustomer3Config>, true> thunker_midOut_2_uMid3;

    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpDpWrapBase<Config>::dpPixelT;
    using typename xpDpWrapBase<Config>::dpSt;

    xpDpWrap(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpDpWrap() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpDpWrap<Config>::xpDpWrap(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpDpWrap", name(), bbMode)
        ,xpDpWrapBase<Config>(name(), variant)
        ,out_0("xpDpMid_out_0", "xpDpSrc")
        ,midOut_0("xpDpChk_midOut_0", "xpDpMid")
        ,out2("xpDpLeaf_out2", "xpDpSrc")
        ,out_1("xpDpChk_out_1", "xpDpLeaf")
        ,out4("xpDpMid_out4", "xpDpSrc")
        ,midOut_1("xpDpChk_midOut_1", "xpDpMid")
        ,out3("xpDpMid_out3", "xpDpSrc")
        ,midOut_2("xpDpChk_midOut_2", "xpDpMid")
        ,uSrc(std::dynamic_pointer_cast<xpDpSrcBase<xpDpTop_xpDpSrcCustomerConfig>>(instanceFactory::createInstance(name(), "uSrc", "xpDpSrc", "customer", "xpDpTop.xpDpTop_xpDpWrap.xpDpTop_xpDpSrc")))
        ,uMid(std::dynamic_pointer_cast<xpDpMidBase<xpDpTop_xpDpMidCustomerConfig<Config>>>(instanceFactory::createInstance<xpDpMid<xpDpTop_xpDpMidCustomerConfig<Config>>>(name(), "uMid", "xpDpMid", variant, "xpDpTop.xpDpTop_xpDpWrap.xpDpMid")))
        ,uChk(std::dynamic_pointer_cast<xpDpChkBase<xpDpTop_xpDpChkCustomerConfig>>(instanceFactory::createInstance(name(), "uChk", "xpDpChk", "customer", "xpDpTop.xpDpTop_xpDpWrap.xpDpTop_xpDpChk")))
        ,uMid2(std::dynamic_pointer_cast<xpDpMidBase<xpDpTop_xpDpMidCustomer2Config>>(instanceFactory::createInstance(name(), "uMid2", "xpDpMid", "customer2", "xpDpTop.xpDpTop_xpDpWrap.xpDpMid")))
        ,uLeafX(std::dynamic_pointer_cast<xpDpLeafBase<xpDpTop_xpDpLeafLeafXConfig<Config>>>(instanceFactory::createInstance<xpDpLeaf<xpDpTop_xpDpLeafLeafXConfig<Config>>>(name(), "uLeafX", "xpDpLeaf", variant, "xpDpTop.xpDpTop_xpDpWrap.xpDpLeaf")))
        ,uChkX(std::dynamic_pointer_cast<xpDpChkBase<xpDpTop_xpDpChkLeafXConfig>>(instanceFactory::createInstance(name(), "uChkX", "xpDpChk", "leafX", "xpDpTop.xpDpTop_xpDpWrap.xpDpTop_xpDpChk")))
        ,uChk2(std::dynamic_pointer_cast<xpDpChkBase<xpDpTop_xpDpChkCustomer2Config>>(instanceFactory::createInstance(name(), "uChk2", "xpDpChk", "customer2", "xpDpTop.xpDpTop_xpDpWrap.xpDpTop_xpDpChk")))
        ,uMid3(std::dynamic_pointer_cast<xpDpMidBase<xpDpTop_xpDpMidCustomer3Config>>(instanceFactory::createInstance(name(), "uMid3", "xpDpMid", "customer3", "xpDpTop.xpDpTop_xpDpWrap.xpDpMid")))
        ,uChk3(std::dynamic_pointer_cast<xpDpChkBase<xpDpTop_xpDpChkCustomer3Config>>(instanceFactory::createInstance(name(), "uChk3", "xpDpChk", "customer3", "xpDpTop.xpDpTop_xpDpWrap.xpDpTop_xpDpChk")))
        ,thunker_out_0_uSrc("thunker_out_0_uSrc", out_0, uSrc->out, name())
        ,thunker_midOut_0_uMid("thunker_midOut_0_uMid", midOut_0, uMid->midOut, name())
        ,thunker_out2_uSrc("thunker_out2_uSrc", out2, uSrc->out2, name())
        ,thunker_out_1_uLeafX("thunker_out_1_uLeafX", out_1, uLeafX->out, name())
        ,thunker_out4_uSrc("thunker_out4_uSrc", out4, uSrc->out4, name())
        ,thunker_midOut_1_uMid2("thunker_midOut_1_uMid2", midOut_1, uMid2->midOut, name())
        ,thunker_out3_uSrc("thunker_out3_uSrc", out3, uSrc->out3, name())
        ,thunker_midOut_2_uMid3("thunker_midOut_2_uMid3", midOut_2, uMid3->midOut, name())
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    uMid->midIn(out_0);
    uChk->in(midOut_0);
    uLeafX->in(out2);
    uChkX->in(out_1);
    uMid2->midIn(out4);
    uChk2->in(midOut_1);
    uMid3->midIn(out3);
    uChk3->in(midOut_2);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

