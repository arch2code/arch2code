//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmVideoSrc --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "raw_channel.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module uvmVideo_uvmVideoSrc.block;
import uvmVideo_uvmVideoSrc.base;
import uvmVideo;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace uvmVideo_ns;
export SC_MODULE(uvmVideoSrc), public blockBase, public uvmVideoSrcBase
{
private:

public:

    uvmVideoSrc(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~uvmVideoSrc() override = default;

    // GENERATED_CODE_END
    // block implementation members

private:
    void sendThread(void);
    void send(bool fv, bool lv, unsigned frame, unsigned line, unsigned beat);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(uvmVideoSrc);

// === Block factory registration (uvmVideoSrc) ===
void register_uvmVideoSrc_variants() {
    instanceFactory::registerBlock("uvmVideoSrc_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmVideoSrc>(blockName, variant, bbMode)); }, "", "uvmVideo");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _uvmVideoSrc_registered = (register_uvmVideoSrc_variants(), 0);
} // namespace
// === End block factory registration ===

uvmVideoSrc::uvmVideoSrc(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("uvmVideoSrc", name(), bbMode)
        ,uvmVideoSrcBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(sendThread);
};

// fv-low clocks before each frame and after the last.
constexpr unsigned FV_LOW_CLOCKS = 4;
// Pixel x of line y of frame f is x + RAMP_PER_LINE * y + RAMP_PER_FRAME * f,
// modulo 256, as a2c_video_cfg's ramp makes it for the UVM bench.
constexpr unsigned RAMP_PER_LINE  = 7;
constexpr unsigned RAMP_PER_FRAME = 13;

// One word per clock: fv low between frames, one fv-high clock before the
// first line and after the last, and two lv-low clocks between lines.
void uvmVideoSrc::sendThread(void)
{
    const unsigned beats = UVM_VIDEO_WIDTH / UVM_VIDEO_PIXELS;
    for (unsigned f = 0; f < UVM_VIDEO_FRAMES; ++f) {
        for (unsigned c = 0; c < FV_LOW_CLOCKS; ++c) send(false, false, f, 0, 0);
        send(true, false, f, 0, 0);
        for (unsigned y = 0; y < UVM_VIDEO_HEIGHT; ++y) {
            if (y != 0) {
                send(true, false, f, y, 0);
                send(true, false, f, y, 0);
            }
            for (unsigned b = 0; b < beats; ++b) send(true, true, f, y, b);
        }
        send(true, false, f, 0, 0);
    }
    for (unsigned c = 0; c < FV_LOW_CLOCKS; ++c) send(false, false, 0, 0, 0);
}

void uvmVideoSrc::send(bool fv, bool lv, unsigned frame, unsigned line, unsigned beat)
{
    uvmVideoRawSt raw;
    raw.fv = fv;
    raw.lv = lv;
    for (unsigned int i = 0; i < UVM_VIDEO_PIXELS; i++) {
        raw.pixels[i] = (fv && lv) ? static_cast<uvmVideoPixelT>(beat * UVM_VIDEO_PIXELS + i + RAMP_PER_LINE * line + RAMP_PER_FRAME * frame) : 0;
    }
    out->write(raw);
}
