//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=tbPeer --mode=module
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
#include "testController.h"
// GENERATED_CODE_BEGIN --template=moduleExport
export module xif_tbPeer.block;
import xif_tbPeer.base;
import xif.tbPeer.config;
import xif;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xif_ns;
export template<typename Config>
SC_MODULE(tbPeer), public blockBase, public tbPeerBase<Config>
{
private:

public:
    SC_HAS_PROCESS(tbPeer);

    // inherited names usable unqualified (no Config:: / this->)
    using tbPeerBase<Config>::DATA_WIDTH;
    using tbPeerBase<Config>::FRAME_HEIGHT;
    using tbPeerBase<Config>::FRAME_WIDTH;
    using tbPeerBase<Config>::out;
    using tbPeerBase<Config>::in;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename tbPeerBase<Config>::streamDataT;
    using typename tbPeerBase<Config>::streamSt;

    tbPeer(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~tbPeer() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    // The frame height this peer resolved from its OWN Config. One peer states
    // it, the other sources it from the testbench container; both must land on
    // the same number, and it is deliberately not the declared default, so a
    // container-sourced parameter that fell back to the default would differ.
    static constexpr uint32_t PEER_FRAME_HEIGHT = FRAME_HEIGHT;
    static constexpr int LOOPCOUNT = 8;
    void outThread(void);
    void inThread(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
tbPeer<Config>::tbPeer(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("tbPeer", name(), bbMode)
        ,tbPeerBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(outThread);
    SC_THREAD(inThread);
};

// Stamp the frame height this peer resolved into the high byte of each payload.
// Driving and receiving are separate threads so the two peers feeding each other
// cannot deadlock on the blocking push.
template<typename Config>
void tbPeer<Config>::outThread(void)
{
    for (int loop = 0; loop < LOOPCOUNT; loop++)
    {
        streamSt t;
        t.data = (PEER_FRAME_HEIGHT << 8) | (loop & 0xFF);
        out->push(t);
    }
}

// Check the sequence and, in the high byte, that the sending peer resolved the
// same frame height this one did.
template<typename Config>
void tbPeer<Config>::inThread(void)
{
    std::string test_name = "test_tb_peer";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    for (int loop = 0; loop < LOOPCOUNT; loop++)
    {
        streamSt t;
        in->pushReceive(t);
        in->ack();
        Q_ASSERT((uint32_t)(t.data & 0xFF) == (uint32_t)(loop & 0xFF),
            "tbPeer stream sequence mismatch");
        Q_ASSERT((uint32_t)(t.data >> 8) == PEER_FRAME_HEIGHT,
            "tbPeer partner resolved a different FRAME_HEIGHT");
    }
    log_.logPrint(std::format("Test {} complete ({})", test_name, this->name()), LOG_ALWAYS);
    controller.test_complete(test_name);
}

