#ifndef BLOCKC_BASE_H
#define BLOCKC_BASE_H

// GENERATED_CODE_PARAM --block=blockC
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "rdy_vld_channel.h"
#include "mixedBlockCIncludes.h"

class blockCBase : public virtual blockPortBase
{
public:
    virtual ~blockCBase() = default;
    // dst ports
    // uBlockA->cStuffIf: An interface for C
    rdy_vld_in< seeSt > see;


    blockCBase(std::string name, const char * variant) :
        see("see")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        see->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        see->setLogging(verbosity);
    };
};
class blockCInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uBlockA->cStuffIf: An interface for C
    rdy_vld_out< seeSt > see;


    blockCInverted(std::string name) :
        see(("see"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        see->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        see->setLogging(verbosity);
    };
};
class blockCChannels
{
public:
    // dst ports
    // An interface for C
    rdy_vld_channel< seeSt > see;


    blockCChannels(std::string name, std::string srcName) :
    see(("see"+name).c_str(), srcName)
    {};
    void bind( blockCBase *a, blockCInverted *b)
    {
        a->see( see );
        b->see( see );
    };
};

// GENERATED_CODE_END

#endif // BLOCKC_BASE_H
