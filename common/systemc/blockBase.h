#ifndef BLOCK_BASE_H
#define BLOCK_BASE_H
//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include "logging.h" // for logBlock
#include "systemc.h"
#if defined(VERILATOR)
#include "verilated_vcd_sc.h"
#endif
#include "timedDelay.h"

enum blockBaseMode {
    BLOCKBASEMODE_NORMAL,
    BLOCKBASEMODE_TANDEM,
    BLOCKBASEMODE_NOFACTORY
};

class blockPortBase
{
public:
    virtual ~blockPortBase() = default;
    virtual void setTimed(int nsec, timedDelayMode mode) = 0;
    virtual void setLogging(verbosity_e verbosity) = 0;
    virtual void setTimedLocal(int nsec, timedDelayMode mode) {}; //function to allow class to override for any class specific functionality
};

class blockBase : public virtual blockPortBase
{
public:
    virtual ~blockBase() = default;
    logBlock log_;
    bool tandem = false;
    std::string tandemName_; // hierarchical name that removes the tandem level
    blockBase(const char* loggingName_, const char* hierarchyName_, blockBaseMode bbMode_=BLOCKBASEMODE_NOFACTORY);
    blockBase(const char* loggingName_, const char* hierarchyName_);
    bool isTandem(void) { return tandem; }
    int getTrackerRefCountDelta(void) { return 2-(int)tandem; } // in tandem mode we need to inc dec by 1 instead of 2
    std::string getAltName(void) { return tandemName_; }
    std::string getAltNameSafe(void)
    {
        std::string ret(tandemName_);
        std::replace(ret.begin(), ret.end(), '.', '_'); // convert . to _ for systemC names
        return ret;
    }
    void setBlockLogging(verbosity_e verbosity) { log_.setVerbosity(verbosity); }

#if defined(VERILATOR)
    virtual void vl_trace(VerilatedVcdC* tfp, int levels, int options = 0) {};
#endif

};
#endif //BLOCK_BASE_H
