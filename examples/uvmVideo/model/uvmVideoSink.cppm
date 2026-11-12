//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmVideoSink --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "axi4_stream_channel.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
#include "testController.h"
// GENERATED_CODE_BEGIN --template=moduleExport
export module uvmVideo_uvmVideoSink.block;
import uvmVideo_uvmVideoSink.base;
import uvmVideo;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace uvmVideo_ns;
export SC_MODULE(uvmVideoSink), public blockBase, public uvmVideoSinkBase
{
private:

public:

    uvmVideoSink(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~uvmVideoSink() override = default;

    // GENERATED_CODE_END
    // block implementation members

private:
    void video_test(void);
    void endOfTestVoter(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(uvmVideoSink);

// === Block factory registration (uvmVideoSink) ===
void register_uvmVideoSink_variants() {
    instanceFactory::registerBlock("uvmVideoSink_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmVideoSink>(blockName, variant, bbMode)); }, "", "uvmVideo");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _uvmVideoSink_registered = (register_uvmVideoSink_variants(), 0);
} // namespace
// === End block factory registration ===

uvmVideoSink::uvmVideoSink(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("uvmVideoSink", name(), bbMode)
        ,uvmVideoSinkBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    ADD_TEST(video_test);
    SC_THREAD(endOfTestVoter);
};

// uSrc's ramp: pixel x of line y of frame f is x + RAMP_PER_LINE * y +
// RAMP_PER_FRAME * f, modulo 256.
constexpr unsigned RAMP_PER_LINE  = 7;
constexpr unsigned RAMP_PER_FRAME = 13;

// Every beat uSrc's frames make: SOF on each frame's first beat only, tlast
// on each line's last beat only, and uSrc's pixel values.
void uvmVideoSink::video_test(void)
{
    const unsigned beats = UVM_VIDEO_WIDTH / UVM_VIDEO_PIXELS;
    for (unsigned f = 0; f < UVM_VIDEO_FRAMES; ++f) {
        for (unsigned y = 0; y < UVM_VIDEO_HEIGHT; ++y) {
            for (unsigned b = 0; b < beats; ++b) {
                axi4StreamInfoSt<uvmVideoBeatSt, uvmVideoIdSt, uvmVideoIdSt, uvmVideoUserSt> beat;
                in->receiveInfo(beat);
                bool sof = y == 0 && b == 0;
                bool last = b + 1 == beats;
                if (bool(beat.tuser.sof) != sof || bool(beat.tlast) != last) {
                    errorCode::fail(std::format("{}: frame {} line {} beat {}: sof {} tlast {}, expected {} and {}", name(), f, y, b,
                                                (unsigned)beat.tuser.sof, (unsigned)beat.tlast, sof, last));
                }
                for (unsigned int i = 0; i < UVM_VIDEO_PIXELS; i++) {
                    uvmVideoPixelT want = static_cast<uvmVideoPixelT>(b * UVM_VIDEO_PIXELS + i + RAMP_PER_LINE * y + RAMP_PER_FRAME * f);
                    if (beat.tdata.pixels[i] != want) {
                        errorCode::fail(std::format("{}: frame {} line {} pixel {} is 0x{:x}, expected 0x{:x}", name(), f, y,
                                                    b * UVM_VIDEO_PIXELS + i, (unsigned)beat.tdata.pixels[i], (unsigned)want));
                    }
                }
            }
        }
    }
    log_.logPrint(std::format("{} checked {} frames", name(), UVM_VIDEO_FRAMES), LOG_IMPORTANT);
}

void uvmVideoSink::endOfTestVoter(void)
{
    endOfTest eot(true);
    testController::GetInstance().wait_all_tests_complete();
    eot.setEndOfTest(true);
}
