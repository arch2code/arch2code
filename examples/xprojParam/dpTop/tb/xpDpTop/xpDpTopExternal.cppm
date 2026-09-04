//

// GENERATED_CODE_PARAM --block=xpDpTop_tb --excludeInst=u_xpDpTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=tbExternalModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "xpDpLeafVariantConfig.h"
#include "push_ack_port_thunker.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=tbExternal
export module xpDpTop.external;
import a2c.endOfTest;
import xpDpTop.base;
import xpDpTop_xpDpTbPeer.base;
import xpDpTop.xpDpTbPeer.config;
import xpDpLeaf;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

using namespace xpDpLeaf_ns;

export class xpDpTopExternal: public sc_module, public xpDpTopInverted {

    logBlock log_;

public:

    std::shared_ptr<xpDpTbPeerBase<xpDpTop_xpDpTbPeerPeerConfig>> uTbPeerA;
    std::shared_ptr<xpDpTbPeerBase<xpDpTop_xpDpTbPeerPeer2Config>> uTbPeerB;

    SC_HAS_PROCESS (xpDpTopExternal);

    xpDpTopExternal(sc_module_name modulename);

    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< dpSt<xpDpTop_xpDpTbPeerPeer2Config> > out_0;
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< dpSt<xpDpTop_xpDpTbPeerPeerConfig> > out_1;

    // cross-interface thunkers
    push_ack_port_thunker<dpSt<xpDpTop_xpDpTbPeerPeer2Config>, dpSt<xpDpTop_xpDpTbPeerPeerConfig>, true> thunker_out_0_uTbPeerA;
    push_ack_port_thunker<dpSt<xpDpTop_xpDpTbPeerPeerConfig>, dpSt<xpDpTop_xpDpTbPeerPeer2Config>, true> thunker_out_1_uTbPeerB;

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

    // GENERATED_CODE_END
    // external implementation members

};

// GENERATED_CODE_BEGIN --template=tbExternal --section=init

xpDpTopExternal::xpDpTopExternal(sc_module_name modulename) :
    xpDpTopInverted("Chnl"),
    log_(name())

   ,uTbPeerA(std::dynamic_pointer_cast<xpDpTbPeerBase<xpDpTop_xpDpTbPeerPeerConfig>>(instanceFactory::createInstance(name(), "uTbPeerA", "xpDpTbPeer", "peer", "xpDpTop.xpDpTop_tb.xpDpTop_xpDpTbPeer")))
   ,uTbPeerB(std::dynamic_pointer_cast<xpDpTbPeerBase<xpDpTop_xpDpTbPeerPeer2Config>>(instanceFactory::createInstance(name(), "uTbPeerB", "xpDpTbPeer", "peer2", "xpDpTop.xpDpTop_tb.xpDpTop_xpDpTbPeer")))
   ,out_0("out_0", "uTbPeerA")
   ,thunker_out_0_uTbPeerA("thunker_out_0_uTbPeerA", out_0, uTbPeerA->out, name())
   ,out_1("out_1", "uTbPeerB")
   ,thunker_out_1_uTbPeerB("thunker_out_1_uTbPeerB", out_1, uTbPeerB->out, name())
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{
    // instance to instance connections via channel
    uTbPeerB->in(out_0);
    uTbPeerA->in(out_1);

    SC_THREAD(eotThread);
    // GENERATED_CODE_END
};

