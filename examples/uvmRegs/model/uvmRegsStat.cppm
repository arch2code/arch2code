//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegsStat --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "apb_channel.h"
#include "rdy_vld_channel.h"
#include "addressMap.h"
#include "hwRegister.h"
#include "hwMemory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module uvmRegs_uvmRegsStat.block;
import uvmRegs_uvmRegsStat.base;
import uvmRegs.uvmRegsStat.config;
import uvmRegs;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace uvmRegs_ns;
export template<typename Config>
SC_MODULE(uvmRegsStat), public blockBase, public uvmRegsStatBase<Config>
{
private:
    void regHandler(void);
    addressMap _a2cRegs;

public:
    SC_HAS_PROCESS(uvmRegsStat);

    // inherited names usable unqualified (no Config:: / this->)
    using uvmRegsStatBase<Config>::UVM_REGS_TAB_W;
    using uvmRegsStatBase<Config>::in;
    using uvmRegsStatBase<Config>::apbReg;
    using uvmRegsStatBase<Config>::out;


    //registers
    hwRegister< uvmRegsModeSt, 4 > mode; // Datapath mode
    hwRegister< uvmRegsCountSt, 4, true > count; // Words passed
    hwRegister< uvmRegsScratchSt, 4 > scratch; // Scratch value the block stores

    memories mems;
    //memories
    hwMemory< uvmRegsWordSt > hist;

    //local memory register infrastructure
    memory_channel< uvmRegsIdxSt, uvmRegsTabSt<Config> > tab_channel;
    memory_out< uvmRegsIdxSt, uvmRegsTabSt<Config> > tab_port;
    hwMemoryPort< uvmRegsIdxSt, uvmRegsTabSt<Config>, 8 > tab_adapter;

    // inherited parameterized types usable unqualified (no <Config>)
    using typename uvmRegsStatBase<Config>::uvmRegsTabT;
    using typename uvmRegsStatBase<Config>::uvmRegsTabSt;

    uvmRegsStat(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~uvmRegsStat() override = default;
    void setTimed(int nsec, timedDelayMode mode) override
    {
        uvmRegsStatBase<Config>::setTimed(nsec, mode);
        mems.setTimed(nsec, mode);
    }

    // GENERATED_CODE_END
    // block implementation members

private:
    // tab's rows, which the register handler reaches through tab_channel.
    std::vector<uvmRegsTabSt> tabRows_;
    uvmRegsWordT words_ = 0;
    void tabService(void);
    void datapath(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
void uvmRegsStat<Config>::regHandler(void) { //handle register decode
    registerHandler< uvmRegsAddrSt, uvmRegsDataSt >(_a2cRegs, this->apbReg, (1<<(8))-1); }

template<typename Config>
uvmRegsStat<Config>::uvmRegsStat(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("uvmRegsStat", name(), bbMode)
        ,uvmRegsStatBase<Config>(name(), variant)
        ,_a2cRegs(log_)
        ,mode(uvmRegsModeSt::_packedSt(0x0))
        ,count()
        ,scratch()
        ,hist(name(), "hist", mems, UVM_REGS_TAB_ROWS, HWMEMORYTYPE_NORMAL, HWMEMORYFWACCESS_RO)
        ,tab_channel("uvmRegsStat_tab", "uvmRegsStat")
        ,tab_port("tab_port")
        ,tab_adapter(tab_port)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // Generated register/memory address offsets
    constexpr uint64_t REG_ADDR_UVMREGSSTAT_HIST = 0x0;
    constexpr uint64_t REG_ADDR_UVMREGSSTAT_TAB = 0x40;
    constexpr uint64_t REG_ADDR_UVMREGSSTAT_MODE = 0x80;
    constexpr uint64_t REG_ADDR_UVMREGSSTAT_COUNT = 0x88;
    constexpr uint64_t REG_ADDR_UVMREGSSTAT_SCRATCH = 0x90;

    // register memories for FW access
    _a2cRegs.addMemory( REG_ADDR_UVMREGSSTAT_HIST, uvmRegsWordSt::_byteWidth, UVM_REGS_TAB_ROWS, std::string(this->name()) + ".hist", &hist);
    _a2cRegs.addMemory( REG_ADDR_UVMREGSSTAT_TAB, 8 * UVM_REGS_TAB_ROWS, std::string(this->name()) + ".tab", &tab_adapter);
    // register registers for FW access
    _a2cRegs.addRegister( REG_ADDR_UVMREGSSTAT_MODE, 1, "mode", &mode );
    _a2cRegs.addRegister( REG_ADDR_UVMREGSSTAT_COUNT, 2, "count", &count );
    _a2cRegs.addRegister( REG_ADDR_UVMREGSSTAT_SCRATCH, 2, "scratch", &scratch );
    // bind local memory register ports to channels
    tab_port(tab_channel);
    SC_THREAD(regHandler);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    // A generated struct's default constructor leaves its fields unset.
    uvmRegsTabSt zero;
    zero.unpack(0);
    tabRows_.assign(UVM_REGS_TAB_ROWS, zero);
    SC_THREAD(tabService);
    SC_THREAD(datapath);
};

template<typename Config>
void uvmRegsStat<Config>::tabService(void)
{
    while (true) {
        bool isWrite = false;
        uvmRegsIdxSt addr;
        uvmRegsTabSt data;
        tab_channel.reqReceive(isWrite, addr, data);
        if (isWrite) {
            tabRows_[addr.idx] = data;
        } else {
            tab_channel.complete(tabRows_[addr.idx]);
        }
    }
}

template<typename Config>
void uvmRegsStat<Config>::datapath(void)
{
    while (true) {
        uvmRegsWordSt w;
        in->read(w);
        uvmRegsIdxT idx = static_cast<uvmRegsIdxT>(w.word & (UVM_REGS_TAB_ROWS - 1));
        hist[idx] = w;
        uvmRegsCountSt c;
        c.count = ++words_;
        count.write(c);
        uvmRegsWordSt o;
        o.word = static_cast<uvmRegsWordT>(w.word ^ tabRows_[idx].entry);
        if (mode.read().invert) {
            o.word = static_cast<uvmRegsWordT>(~o.word);
        }
        out->write(o);
    }
}
