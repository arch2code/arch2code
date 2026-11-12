//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmVideo --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "axi4_stream_channel.h"
#include "raw_channel.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module uvmVideo.block;
import uvmVideo.base;
import uvmVideo;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace uvmVideo_ns;
export SC_MODULE(uvmVideo), public blockBase, public uvmVideoBase
{
private:

public:

    uvmVideo(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~uvmVideo() override = default;

    // GENERATED_CODE_END
    // block implementation members

private:
    void videoThread(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(uvmVideo);

// === Block factory registration (uvmVideo) ===
void register_uvmVideo_variants() {
    instanceFactory::registerBlock("uvmVideo_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmVideo>(blockName, variant, bbMode)); }, "", "uvmVideo");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _uvmVideo_registered = (register_uvmVideo_variants(), 0);
} // namespace
// === End block factory registration ===

uvmVideo::uvmVideo(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("uvmVideo", name(), bbMode)
        ,uvmVideoBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(videoThread);
};

// One raw word per clock. Each pixel beat is held until the next word shows
// whether lv or fv fell after it, which sets tlast, as the RTL does.
void uvmVideo::videoThread(void)
{
    bool first = true;
    bool heldVld = false;
    bool heldSof = false;
    uvmVideoBeatSt held;
    while (true) {
        uvmVideoRawSt raw;
        vin->read(raw);
        bool pix = raw.fv && raw.lv;
        if (heldVld) {
            axi4StreamInfoSt<uvmVideoBeatSt, uvmVideoIdSt, uvmVideoIdSt, uvmVideoUserSt> beat;
            beat.tdata = held;
            for (unsigned int i = 0; i < uvmVideoBeatSt::_byteWidth; i++) {
                beat.tstrb[i] = Q_TRUE;
                beat.tkeep[i] = Q_TRUE;
            }
            beat.tid.id = 0;
            beat.tdest.id = 0;
            beat.tuser.sof = heldSof;
            beat.tlast = !pix;
            vout->sendInfo(beat);
        }
        heldVld = pix;
        if (pix) {
            for (unsigned int i = 0; i < UVM_VIDEO_PIXELS; i++) {
                held.pixels[i] = raw.pixels[i];
            }
            heldSof = first;
        }
        first = !raw.fv || (first && !pix);
    }
}
