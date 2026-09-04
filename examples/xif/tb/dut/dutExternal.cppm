//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=xif_tb --excludeInst=uDut --mode=module --variant=tbV0
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=tbExternalModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "xifVariantConfig.h"
#include "push_ack_port_thunker.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=tbExternal
export module xif_dut.external;
import a2c.endOfTest;
import xif_dut.base;
import xif_tbPeer.base;
import xif_src.base;
import xif_sink.base;
import xif_tbPeer.block;
import xif;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

using namespace xif_ns;

export class dutExternal: public sc_module, public dutInverted<dutDutV0Config> {

    logBlock log_;

public:

    std::shared_ptr<tbPeerBase<tbPeerPv0Config>> uTbPeerA;
    std::shared_ptr<tbPeerBase<tbPeerPvSourcedConfig<xif_tbTbV0Config>>> uTbPeerB;
    std::shared_ptr<srcBase<srcSrcV0Config>> uSrc;
    std::shared_ptr<sinkBase<sinkSinkV0Config>> uSink;

    SC_HAS_PROCESS (dutExternal);

    dutExternal(sc_module_name modulename);

    // Parameterized DUT stream (also the connection interface A)
    push_ack_channel< streamSt<tbPeerPvSourcedConfig<xif_tbTbV0Config>> > out_0;
    // Parameterized DUT stream (also the connection interface A)
    push_ack_channel< streamSt<tbPeerPv0Config> > out_1;

    // cross-interface thunkers
    push_ack_port_thunker<streamSt<tbPeerPvSourcedConfig<xif_tbTbV0Config>>, streamSt<tbPeerPv0Config>, true> thunker_out_0_uTbPeerA;
    push_ack_port_thunker<streamSt<tbPeerPv0Config>, streamSt<tbPeerPvSourcedConfig<xif_tbTbV0Config>>, true> thunker_out_1_uTbPeerB;
    push_ack_port_thunker<streamSt<dutDutV0Config>, streamBndrySt, false> thunker_out_uSrc;
    push_ack_port_thunker<streamSt<dutDutV0Config>, streamBndrySt, false> thunker_streamOut_uSink;

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

    // GENERATED_CODE_END
    // external implementation members

};

// GENERATED_CODE_BEGIN --template=tbExternal --section=init

dutExternal::dutExternal(sc_module_name modulename) :
    dutInverted<dutDutV0Config>("Chnl"),
    log_(name())

   ,uTbPeerA(std::dynamic_pointer_cast<tbPeerBase<tbPeerPv0Config>>(instanceFactory::createInstance(name(), "uTbPeerA", "tbPeer", "pv0", "xif.xif_tb.xif_tbPeer")))
   ,uTbPeerB(std::dynamic_pointer_cast<tbPeerBase<tbPeerPvSourcedConfig<xif_tbTbV0Config>>>(instanceFactory::createInstance<tbPeer<tbPeerPvSourcedConfig<xif_tbTbV0Config>>>(name(), "uTbPeerB", "tbPeer", "pvSourced", "xif.xif_tb.xif_tbPeer")))
   ,uSrc(std::dynamic_pointer_cast<srcBase<srcSrcV0Config>>(instanceFactory::createInstance(name(), "uSrc", "src", "srcV0", "xif.xif_tb.xif_src")))
   ,uSink(std::dynamic_pointer_cast<sinkBase<sinkSinkV0Config>>(instanceFactory::createInstance(name(), "uSink", "sink", "sinkV0", "xif.xif_tb.xif_sink")))
   ,out_0("out_0", "uTbPeerA")
   ,thunker_out_0_uTbPeerA("thunker_out_0_uTbPeerA", out_0, uTbPeerA->out, name())
   ,out_1("out_1", "uTbPeerB")
   ,thunker_out_1_uTbPeerB("thunker_out_1_uTbPeerB", out_1, uTbPeerB->out, name())
   ,thunker_out_uSrc("thunker_out_uSrc", streamIn, uSrc->out, name())
   ,thunker_streamOut_uSink("thunker_streamOut_uSink", streamOut, uSink->in, name())
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{
    // instance to instance connections via channel
    uTbPeerB->in(out_0);
    uTbPeerA->in(out_1);

    SC_THREAD(eotThread);
    // GENERATED_CODE_END
};

