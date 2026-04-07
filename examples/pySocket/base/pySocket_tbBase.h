#ifndef PYSOCKET_TB_BASE_H
#define PYSOCKET_TB_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=pySocket_tb
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "req_ack_channel.h"
#include "pySocketIncludes.h"

class pySocket_tbBase : public virtual blockPortBase
{
public:
    virtual ~pySocket_tbBase() = default;


    pySocket_tbBase(std::string name, const char * variant) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
class pySocket_tbInverted : public virtual blockPortBase
{
public:


    pySocket_tbInverted(std::string name) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
class pySocket_tbChannels
{
public:


    pySocket_tbChannels(std::string name, std::string srcName) 
    {};
    void bind( pySocket_tbBase *a, pySocket_tbInverted *b)
    {
    };
};

// GENERATED_CODE_END
#endif //PYSOCKET_TB_BASE_H
