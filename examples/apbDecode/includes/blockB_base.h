#ifndef BLOCKB_BASE_H
#define BLOCKB_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=blockB
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "apb_channel.h"
#include "apbDecodeIncludes.h"

class blockBBase : public virtual blockPortBase
{
public:
    virtual ~blockBBase() = default;
    // src ports

    // dst ports
    // uAPBDecode->apbReg: CPU access to SoC registers in the design
    apb_in< apbAddrSt, apbDataSt > apbReg;


    blockBBase(std::string name, const char * variant) :
        apbReg("apbReg")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbReg->setLogging(verbosity);
    };
};
class blockBInverted : public virtual blockPortBase
{
public:
    // src ports

    // dst ports
    // uAPBDecode->apbReg: CPU access to SoC registers in the design
    apb_out< apbAddrSt, apbDataSt > apbReg;


    blockBInverted(std::string name) :
        apbReg(("apbReg"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbReg->setLogging(verbosity);
    };
};
class blockBChannels
{
public:
    // src ports

    // dst ports
    //   apbReg
    apb_channel< apbAddrSt, apbDataSt > apbReg;


    blockBChannels(std::string name, std::string srcName) :
    apbReg(("apbReg"+name).c_str(), srcName)
    {};
    void bind( blockBBase *a, blockBInverted *b)
    {
        a->apbReg( apbReg );
        b->apbReg( apbReg );
    };
};

// GENERATED_CODE_END

#endif //BLOCKB_BASE_H
