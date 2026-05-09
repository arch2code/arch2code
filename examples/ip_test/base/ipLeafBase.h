#ifndef IPLEAF_BASE_H
#define IPLEAF_BASE_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=ipLeaf
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "blockBase.h"
import ipLeaf;
using namespace ipLeaf_ns;

template<typename Config>
class ipLeafBase : public virtual blockPortBase
{
public:
    virtual ~ipLeafBase() = default;
    const uint64_t LEAF_DATA_WIDTH;
    const uint64_t LEAF_MEM_DEPTH;


    ipLeafBase(std::string name, const char * variant) :
        LEAF_DATA_WIDTH(Config::LEAF_DATA_WIDTH)
        ,LEAF_MEM_DEPTH(Config::LEAF_MEM_DEPTH)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
template<typename Config>
class ipLeafInverted : public virtual blockPortBase
{
public:


    ipLeafInverted(std::string name) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
template<typename Config>
class ipLeafChannels
{
public:


    ipLeafChannels(std::string name, std::string srcName) 
    {};
    void bind( ipLeafBase<Config> *a, ipLeafInverted<Config> *b)
    {
    };
};

// GENERATED_CODE_END
#endif //IPLEAF_BASE_H
