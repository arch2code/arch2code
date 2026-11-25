//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockA --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "apb_channel.h"
#include "addressMap.h"
#include "hwRegister.h"
#include "hwMemory.h"
// GENERATED_CODE_END
// user #includes here
#include "q_assert.h"
// GENERATED_CODE_BEGIN --template=moduleExport
export module apbDecode_blockA.block;
import apbDecode_blockA.base;
import apbDecode;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace apbDecode_ns;
export SC_MODULE(blockA), public blockBase, public blockABase
{
private:
    void regHandler(void);
    addressMap _a2cRegs;

public:

    //registers
    hwRegister< aRegSt, 8, true > roA; // A Read Only register
    hwRegister< un0ARegSt, 8 > rwUn0A; // A unaligned Read Write register
    hwRegister< un0ARegSt, 8, true > roUn0A; // A unaligned Read Only register
    hwRegister< un0ExtRegSt, 4 > extA; // A unaligned Read Only register defined externally
    std::array< hwRegister< arrRegSt, 4 >, REGARR_N > rwArr; // A Read Write register array
    std::array< hwRegister< arrRegSt, 4, true >, REGARR_N > roArr; // A Read Only register array

    memories mems;
    //memories
    hwMemory< aMemSt > blockATable0;
    hwMemory< aMemSt > blockATableX;
    hwMemory< aMemSt > blockATable1;

    blockA(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockA() override = default;
    void setTimed(int nsec, timedDelayMode mode) override
    {
        blockABase::setTimed(nsec, mode);
        mems.setTimed(nsec, mode);
    }

    // GENERATED_CODE_END
    // block implementation members
    // The bits of field d of arrRegSt: unpacking all ones masks each field to its own width.
    static inline const uint32_t D_MASK = [] { arrRegSt m; m.unpack(arrRegSt::_packedSt(~arrRegSt::_packedSt(0))); return uint32_t(m.d); }();

private:
    void LocalRegAccess();
    // roArr[i] = rwArr[(i+1) % N] + i + ROARR_BIAS, recomputed when any rwArr element is written.
    void arrDrive();
    sc_event rwArrWritten_;
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(blockA);

// === Block factory registration (blockA) ===
void register_blockA_variants() {
    instanceFactory::registerBlock("blockA_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockA>(blockName, variant, bbMode)); }, "", "apbDecode");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _blockA_registered = (register_blockA_variants(), 0);
} // namespace
// === End block factory registration ===

void blockA::regHandler(void) { //handle register decode
    registerHandler< apbAddrSt, apbDataSt >(_a2cRegs, apbReg, (1<<(10))-1); }

blockA::blockA(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockA", name(), bbMode)
        ,blockABase(name(), variant)
        ,_a2cRegs(log_)
        ,roA()
        ,rwUn0A(un0ARegSt::_packedSt(0x1234abcdef))
        ,roUn0A()
        ,extA()
        ,rwArr{ { arrRegSt::_packedSt(0x0), arrRegSt::_packedSt(0x0), arrRegSt::_packedSt(0x0), arrRegSt::_packedSt(0x0) } }
        ,roArr()
        ,blockATable0(name(), "blockATable0", mems, MEMORYA_WORDS)
        ,blockATableX(name(), "blockATableX", mems, MEMORYA_WORDS)
        ,blockATable1(name(), "blockATable1", mems, MEMORYA_WORDS)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // Generated register/memory address offsets
    constexpr uint64_t REG_ADDR_BLOCKA_BLOCKATABLE0 = 0x0;
    constexpr uint64_t REG_ADDR_BLOCKA_BLOCKATABLE1 = 0x100;
    constexpr uint64_t REG_ADDR_BLOCKA_RWARR = 0x200;
    constexpr uint64_t REG_ADDR_BLOCKA_RWARR_STRIDE = 0x8;
    constexpr uint64_t REG_ADDR_BLOCKA_ROARR = 0x220;
    constexpr uint64_t REG_ADDR_BLOCKA_ROARR_STRIDE = 0x8;
    constexpr uint64_t REG_ADDR_BLOCKA_ROA = 0x240;
    constexpr uint64_t REG_ADDR_BLOCKA_RWUN0A = 0x248;
    constexpr uint64_t REG_ADDR_BLOCKA_ROUN0A = 0x250;
    constexpr uint64_t REG_ADDR_BLOCKA_EXTA = 0x258;

    // register memories for FW access
    _a2cRegs.addMemory( REG_ADDR_BLOCKA_BLOCKATABLE0, aMemSt::_byteWidth, MEMORYA_WORDS, std::string(this->name()) + ".blockATable0", &blockATable0);
    _a2cRegs.addMemory( REG_ADDR_BLOCKA_BLOCKATABLE1, aMemSt::_byteWidth, MEMORYA_WORDS, std::string(this->name()) + ".blockATable1", &blockATable1);
    // register registers for FW access
    for (uint32_t i = 0; i < REGARR_N; i++)
        _a2cRegs.addRegister( REG_ADDR_BLOCKA_RWARR + i * REG_ADDR_BLOCKA_RWARR_STRIDE, 2, std::format("rwArr[{}]", i), &rwArr[i] );
    for (uint32_t i = 0; i < REGARR_N; i++)
        _a2cRegs.addRegister( REG_ADDR_BLOCKA_ROARR + i * REG_ADDR_BLOCKA_ROARR_STRIDE, 2, std::format("roArr[{}]", i), &roArr[i] );
    _a2cRegs.addRegister( REG_ADDR_BLOCKA_ROA, 5, "roA", &roA );
    _a2cRegs.addRegister( REG_ADDR_BLOCKA_RWUN0A, 6, "rwUn0A", &rwUn0A );
    _a2cRegs.addRegister( REG_ADDR_BLOCKA_ROUN0A, 6, "roUn0A", &roUn0A );
    _a2cRegs.addRegister( REG_ADDR_BLOCKA_EXTA, 4, "extA", &extA );
    SC_THREAD(regHandler);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(LocalRegAccess);
    for (auto &r : rwArr) r.registerEvent(&rwArrWritten_);
    SC_THREAD(arrDrive);
};

// blockA reads rwArr and drives roArr.
void blockA::arrDrive() {
    for (;;) {
        for (uint32_t i = 0; i < REGARR_N; i++) {
            arrRegSt v;
            v.d = (rwArr[(i + 1) % REGARR_N].read().d + i + ROARR_BIAS) & D_MASK;
            roArr[i].write(v);
        }
        wait(rwArrWritten_);
    }
}

// Local register/memory access api using native data types
void blockA::LocalRegAccess() {

    // Register
    un0ExtRegSt arw;

    arw.fa = 'a';
    arw.fb = 0x1234;
    arw.fc = 'c';

    extA.write(arw);

    // Memory
    aMemSt readData, writeData;

    writeData.data = 0x2a782d645e49c378;

    blockATable1[0x5].data = writeData.data;
    readData = blockATable1[0x5];

    Q_ASSERT(readData == writeData, "readData.data == writeData.data");

};

