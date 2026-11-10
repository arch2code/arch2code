//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockD --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "external_reg_channel.h"
#include "memory_channel.h"
#include "rdy_vld_channel.h"
#include "req_ack_channel.h"
#include "status_channel.h"
// GENERATED_CODE_END
#include "testController.h"
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module mixed_blockD.block;
import mixed_blockD.base;
import mixed;
import mixed_mixedBlockC;
import mixed_mixedInclude;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace mixed_ns;
using namespace mixed_mixedBlockC_ns;
using namespace mixed_mixedInclude_ns;
export SC_MODULE(blockD), public blockBase, public blockDBase
{
private:

public:

    blockD(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockD() override = default;

    // GENERATED_CODE_END
    // block implementation members

    void test_mem_hier_blockd_write(void);
    void test_mem_hier_blockd_read(void);
    
    // Memory register handler for blockBTableExt.
    // This services register accesses to blockBTableExt through the memory port.
    void blockBTableExtModel(void);
    std::vector<seeSt> blockBTableExt_shadow_;
    
    // Memory register handler for blockBTable37Bit.
    // This services register accesses to blockBTable37Bit through the memory port.
    void blockBTable37BitModel(void);
    std::vector<test37BitRegSt> blockBTable37Bit_shadow_;

    // extArr model, as the RTL: rdata = last written wdata + current rwArr + index, recomputed whenever either changes.
    void extModel(int i, external_reg_in<dRegSt>& p);
    void extRwTrack(void);
    std::array<dRegSt, REGARR_N> extWdata_{};
    // The bits of field d of dRegSt: unpacking all ones masks each field to its own width.
    static inline const uint32_t D_MASK = [] { dRegSt m; m.unpack(dRegSt::_packedSt(~dRegSt::_packedSt(0))); return uint32_t(m.d); }();
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(blockD);

// === Block factory registration (blockD) ===
void register_blockD_variants() {
    instanceFactory::registerBlock("blockD_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockD>(blockName, variant, bbMode)); }, "", "mixed");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _blockD_registered = (register_blockD_variants(), 0);
} // namespace
// === End block factory registration ===

blockD::blockD(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockD", name(), bbMode)
        ,blockDBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    ADD_TEST(test_mem_hier_blockd_write);
    ADD_TEST(test_mem_hier_blockd_read);
    SC_THREAD(blockBTableExtModel);
    SC_THREAD(blockBTable37BitModel);
    for (size_t i = 0; i < REGARR_N; i++) {
        sc_spawn([this, i]() { extModel(i, extArr[i]); }, sc_gen_unique_name("extModel", false));
    }
    SC_THREAD(extRwTrack);
    
    // Model-backed storage for memory register blockBTableExt (BSIZE wordlines).
    // Default init: all zeros.
    blockBTableExt_shadow_.assign(BSIZE, seeSt());
    
    // Model-backed storage for memory register blockBTable37Bit (BSIZE wordlines).
    // Initialize with test pattern (index << 32) | index
    blockBTable37Bit_shadow_.assign(BSIZE, test37BitRegSt());
    for (uint32_t i = 0; i < BSIZE; i++) {
        uint64_t val = (static_cast<uint64_t>(i) << 32) | i;
        blockBTable37Bit_shadow_[i].value37 = val & 0x1FFFFFFFFF;
    }
};

void blockD::test_mem_hier_blockd_write(void)
{
    wait(1, SC_NS);

    bSizeSt addr;
    addr.index = 0;
    bigSt data;
    
    data.big = 0x1234567812345678;
    blockBTable1->request(true, addr, data);
    log_.logPrint("BlockD Write complete", LOG_ALWAYS);
}

void blockD::test_mem_hier_blockd_read(void)
{
    bSizeSt addr;
    addr.index = 0;
    bigSt data;

    blockBTable1->request(false, addr, data);
    
    if (data.big == 0x1234567812345678) {
        log_.logPrint("BlockD Read verify success", LOG_ALWAYS);
    } else {
        std::stringstream ss;
        ss << "BlockD Read verify failed. Expected 0x1234567812345678, got 0x" << std::hex << data.big;
        log_.logPrint(ss.str(), LOG_ALWAYS);
    }
}

void blockD::extModel(int i, external_reg_in<dRegSt>& p)
{
    // Publish the readback for the stored wdata and the rwArr value that is current now.
    auto publish = [this, i, &p]() {
        dRegSt r;
        r.d = (extWdata_[i].d + rwArr->readNonBlocking().d + i) & D_MASK;
        p->update_mirror(r);
    };
    publish();
    while (true) {
        dRegSt w;
        p->read(w);
        extWdata_[i] = w;
        publish();
        log_.logPrint(std::format("{} extArr[{}] write 0x{:02x} rwArr 0x{:02x}", name(), i,
                                  static_cast<unsigned>(w.d), static_cast<unsigned>(rwArr->readNonBlocking().d)), LOG_ALWAYS);
    }
}

// A change of rwArr moves every ext readback, as the combinational RTL does.
void blockD::extRwTrack(void)
{
    while (true) {
        rwArr->read();
        for (int i = 0; i < static_cast<int>(REGARR_N); i++) {
            dRegSt r;
            r.d = (extWdata_[i].d + rwArr->readNonBlocking().d + i) & D_MASK;
            extArr[i]->update_mirror(r);
        }
    }
}

void blockD::blockBTableExtModel(void)
{
    while (true) {
        bool isWrite = false;
        bSizeSt addr;
        seeSt data;

        // Wait for a request from the memory register port.
        blockBTableExt->reqReceive(isWrite, addr, data);

        const uint32_t idx = static_cast<uint32_t>(addr.index);
        if (idx >= blockBTableExt_shadow_.size()) {
            log_.logPrint(std::format("blockBTableExtModel: addr out of range idx={}", idx), LOG_ALWAYS);
            if (!isWrite) {
                blockBTableExt->complete(seeSt());
            }
            continue;
        }

        if (isWrite) {
            // Writes are acknowledged via complete with default constructed value
            blockBTableExt_shadow_[idx] = data;
            // For writes, complete is called automatically or we need to call it
            // (depending on interface semantics, but usually not needed for writes)
        } else {
            // Complete reads with the current model value.
            blockBTableExt->complete(blockBTableExt_shadow_[idx]);
        }
    }
}

void blockD::blockBTable37BitModel(void)
{
    while (true) {
        bool isWrite = false;
        bSizeSt addr;
        test37BitRegSt data;

        // Wait for a request from the memory register port.
        blockBTable37Bit->reqReceive(isWrite, addr, data);

        const uint32_t idx = static_cast<uint32_t>(addr.index);
        if (idx >= blockBTable37Bit_shadow_.size()) {
            log_.logPrint(std::format("blockBTable37BitModel: addr out of range idx={}", idx), LOG_ALWAYS);
            if (!isWrite) {
                blockBTable37Bit->complete(test37BitRegSt());
            }
            continue;
        }

        if (isWrite) {
            // Store write data to shadow storage
            blockBTable37Bit_shadow_[idx] = data;
            log_.logPrint(std::format("blockBTable37BitModel: Write idx={} val=0x{:x}", idx, data.value37), LOG_DEBUG);
        } else {
            // Complete reads with the current model value.
            blockBTable37Bit->complete(blockBTable37Bit_shadow_[idx]);
            log_.logPrint(std::format("blockBTable37BitModel: Read idx={} val=0x{:x}", idx, blockBTable37Bit_shadow_[idx].value37), LOG_DEBUG);
        }
    }
}

