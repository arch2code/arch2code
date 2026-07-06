//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=gen
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "gen.h"
SC_HAS_PROCESS(gen);

// === Block factory registration (gen) ===
void register_gen_variants() {
    instanceFactory::registerBlock("gen_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<gen>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _gen_registered = (register_gen_variants(), 0);
} // namespace
// === End block factory registration ===

gen::gen(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("gen", name(), bbMode)
        ,genBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    // This gen instance is one end-of-test voter; it casts its vote in recv().
    eot_.registerVoter();
    SC_THREAD(send);
    SC_THREAD(recv);
};

// Drive LOOPCOUNT words out of dOut into the leaf pipeline.
void gen::send(void)
{
    for (int i = 0; i < LOOPCOUNT; i++)
    {
        dat_st w;
        w.d = i;
        dOut->push(w);
    }
}

// Receive the words looped back on dIn (after passing through both leaf
// stages), verify the sequence, then vote end-of-test.
void gen::recv(void)
{
    for (int i = 0; i < LOOPCOUNT; i++)
    {
        dat_st w;
        dIn->pushReceive(w);
        dIn->ack();
        Q_ASSERT(w.d == (dat)i, "looped-back data mismatch");
    }
    log_.logPrint(std::format("{} verified {} words round-trip", this->name(), LOOPCOUNT), LOG_ALWAYS);
    eot_.setEndOfTest(true);
};

