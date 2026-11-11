//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockBRegs --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"
#include "external_reg_channel.h"
#include "memory_channel.h"
#include "status_channel.h"

export module mixed_blockBRegs.base;
import mixed;
import mixed_mixedBlockC;
import mixed_mixedInclude;
using namespace mixed_ns;
using namespace mixed_mixedBlockC_ns;
using namespace mixed_mixedInclude_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class blockBRegsBase : public virtual blockPortBase
{
public:
    virtual ~blockBRegsBase() = default;
    // src ports
    // blockB->reg(rwD) A Read Write register
    status_out< dRegSt > rwD;
    // blockB->reg(blockBTableExt) Memory register - firmware accessible memory-mapped storage
    memory_out< bSizeSt, seeSt > blockBTableExt;
    // blockB->reg(blockBTable37Bit) External 37-bit memory register - firmware accessible with 8-byte stride
    memory_out< bSizeSt, test37BitRegSt > blockBTable37Bit;
    // blockB->reg(rwArr) A Read Write register array
    sc_vector< status_out< dRegSt > > rwArr;
    // blockB->reg(extArr) An External register array
    sc_vector< external_reg_out< dRegSt > > extArr;
    // blockB->reg(extFArr) An External register array with one element per blockF instance
    sc_vector< external_reg_out< dRegSt > > extFArr;
    // blockB->mem(blockBTable1) Dual Port with one connection
    memory_out< bSizeSt, bigSt > blockBTable1;

    // dst ports
    // External->apbReg: CPU access to SoC registers in the design
    apb_in< apbAddrSt, apbDataSt > apbReg;
    // blockB->reg(roBsize) A Read Only register with a structure that has a definition from an included context
    status_in< bSizeRegSt > roBsize;


    blockBRegsBase(std::string name, const char * variant) :
        rwD("rwD")
        ,blockBTableExt("blockBTableExt")
        ,blockBTable37Bit("blockBTable37Bit")
        ,rwArr("rwArr", REGARR_N)
        ,extArr("extArr", REGARR_N)
        ,extFArr("extFArr", EXTFARR_N)
        ,blockBTable1("blockBTable1")
        ,apbReg("apbReg")
        ,roBsize("roBsize")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        rwD->setTimed(nsec, mode);
        blockBTableExt->setTimed(nsec, mode);
        blockBTable37Bit->setTimed(nsec, mode);
        for (auto & p : rwArr) p->setTimed(nsec, mode);
        for (auto & p : extArr) p->setTimed(nsec, mode);
        for (auto & p : extFArr) p->setTimed(nsec, mode);
        blockBTable1->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        roBsize->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        rwD->setLogging(verbosity);
        blockBTableExt->setLogging(verbosity);
        blockBTable37Bit->setLogging(verbosity);
        for (auto & p : rwArr) p->setLogging(verbosity);
        for (auto & p : extArr) p->setLogging(verbosity);
        for (auto & p : extFArr) p->setLogging(verbosity);
        blockBTable1->setLogging(verbosity);
        apbReg->setLogging(verbosity);
        roBsize->setLogging(verbosity);
    };
};
export class blockBRegsInverted : public virtual blockPortBase
{
public:
    // src ports
    // blockB->reg(rwD) A Read Write register
    status_in< dRegSt > rwD;
    // blockB->reg(blockBTableExt) Memory register - firmware accessible memory-mapped storage
    memory_in< bSizeSt, seeSt > blockBTableExt;
    // blockB->reg(blockBTable37Bit) External 37-bit memory register - firmware accessible with 8-byte stride
    memory_in< bSizeSt, test37BitRegSt > blockBTable37Bit;
    // blockB->reg(rwArr) A Read Write register array
    sc_vector< status_in< dRegSt > > rwArr;
    // blockB->reg(extArr) An External register array
    sc_vector< external_reg_in< dRegSt > > extArr;
    // blockB->reg(extFArr) An External register array with one element per blockF instance
    sc_vector< external_reg_in< dRegSt > > extFArr;
    // blockB->mem(blockBTable1) Dual Port with one connection
    memory_in< bSizeSt, bigSt > blockBTable1;

    // dst ports
    // External->apbReg: CPU access to SoC registers in the design
    apb_out< apbAddrSt, apbDataSt > apbReg;
    // blockB->reg(roBsize) A Read Only register with a structure that has a definition from an included context
    status_out< bSizeRegSt > roBsize;


    blockBRegsInverted(std::string name) :
        rwD(("rwD"+name).c_str())
        ,blockBTableExt(("blockBTableExt"+name).c_str())
        ,blockBTable37Bit(("blockBTable37Bit"+name).c_str())
        ,rwArr(("rwArr"+name).c_str(), REGARR_N)
        ,extArr(("extArr"+name).c_str(), REGARR_N)
        ,extFArr(("extFArr"+name).c_str(), EXTFARR_N)
        ,blockBTable1(("blockBTable1"+name).c_str())
        ,apbReg(("apbReg"+name).c_str())
        ,roBsize(("roBsize"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        rwD->setTimed(nsec, mode);
        blockBTableExt->setTimed(nsec, mode);
        blockBTable37Bit->setTimed(nsec, mode);
        for (auto & p : rwArr) p->setTimed(nsec, mode);
        for (auto & p : extArr) p->setTimed(nsec, mode);
        for (auto & p : extFArr) p->setTimed(nsec, mode);
        blockBTable1->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        roBsize->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        rwD->setLogging(verbosity);
        blockBTableExt->setLogging(verbosity);
        blockBTable37Bit->setLogging(verbosity);
        for (auto & p : rwArr) p->setLogging(verbosity);
        for (auto & p : extArr) p->setLogging(verbosity);
        for (auto & p : extFArr) p->setLogging(verbosity);
        blockBTable1->setLogging(verbosity);
        apbReg->setLogging(verbosity);
        roBsize->setLogging(verbosity);
    };
};
export class blockBRegsChannels
{
public:
    // src ports
    // A Read Write register
    status_channel< dRegSt > rwD;
    // Memory register - firmware accessible memory-mapped storage
    memory_channel< bSizeSt, seeSt > blockBTableExt;
    // External 37-bit memory register - firmware accessible with 8-byte stride
    memory_channel< bSizeSt, test37BitRegSt > blockBTable37Bit;
    // A Read Write register array
    sc_vector< status_channel< dRegSt > > rwArr;
    // An External register array
    sc_vector< external_reg_channel< dRegSt > > extArr;
    // An External register array with one element per blockF instance
    sc_vector< external_reg_channel< dRegSt > > extFArr;
    // Dual Port with one connection
    memory_channel< bSizeSt, bigSt > blockBTable1;

    // dst ports
    // CPU access to SoC registers in the design
    apb_channel< apbAddrSt, apbDataSt > apbReg;
    // A Read Only register with a structure that has a definition from an included context
    status_channel< bSizeRegSt > roBsize;


    blockBRegsChannels(std::string name, std::string srcName) :
    rwD(("rwD"+name).c_str(), srcName)
    ,blockBTableExt(("blockBTableExt"+name).c_str(), srcName)
    ,blockBTable37Bit(("blockBTable37Bit"+name).c_str(), srcName)
    ,rwArr(("rwArr"+name).c_str(), REGARR_N, [&](const char * nm, size_t) { return new status_channel< dRegSt >(nm, srcName); })
    ,extArr(("extArr"+name).c_str(), REGARR_N, [&](const char * nm, size_t) { return new external_reg_channel< dRegSt >(nm, srcName); })
    ,extFArr(("extFArr"+name).c_str(), EXTFARR_N, [&](const char * nm, size_t) { return new external_reg_channel< dRegSt >(nm, srcName); })
    ,blockBTable1(("blockBTable1"+name).c_str(), srcName)
    ,apbReg(("apbReg"+name).c_str(), srcName)
    ,roBsize(("roBsize"+name).c_str(), srcName)
    {};
    void bind( blockBRegsBase *a, blockBRegsInverted *b)
    {
        a->rwD( rwD );
        b->rwD( rwD );
        a->blockBTableExt( blockBTableExt );
        b->blockBTableExt( blockBTableExt );
        a->blockBTable37Bit( blockBTable37Bit );
        b->blockBTable37Bit( blockBTable37Bit );
        a->rwArr.bind( rwArr );
        b->rwArr.bind( rwArr );
        a->extArr.bind( extArr );
        b->extArr.bind( extArr );
        a->extFArr.bind( extFArr );
        b->extFArr.bind( extFArr );
        a->blockBTable1( blockBTable1 );
        b->blockBTable1( blockBTable1 );
        a->apbReg( apbReg );
        b->apbReg( apbReg );
        a->roBsize( roBsize );
        b->roBsize( roBsize );
    };
};

// GENERATED_CODE_END
