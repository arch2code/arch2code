#ifndef LOGGING_H
#define LOGGING_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include "log.h"
#include <string>
#include <sstream>
#include <mutex>
#include <unordered_map>
#include <vector>
#include <functional>
#include "q_assert.h"
#include <iomanip>
#include <atomic>
#include <fmt/format.h>

const int unsigned MAX_DUMP_HALF_LIMIT = 5;

template<typename T, int unsigned M>
inline static std::string staticArrayPrt(const T* array, bool dumpAll = false) {
    if ( dumpAll == true || M <= (2*MAX_DUMP_HALF_LIMIT) || MAX_DUMP_HALF_LIMIT == 0 ) {
        std::ostringstream oss;
        const T* ptr = array;
        for(int unsigned i=0; i<M; i++) {
            bool is_join = ( i+1 == M );
            oss << std::hex << std::setw(sizeof(T)*2) << std::setfill('0') << (uint64_t) *ptr++ << (is_join ? "" : " ");
        }
        return oss.str();
    } else {
        std::ostringstream oss_l;
        std::ostringstream oss_h;
        const T* ptr_l = array;
        const T* ptr_h = array + M - MAX_DUMP_HALF_LIMIT;
        for(int unsigned i=0; i<MAX_DUMP_HALF_LIMIT; i++) {
            bool is_join = ( i+1 == MAX_DUMP_HALF_LIMIT );
            oss_l << std::hex << std::setw(sizeof(T)*2) << std::setfill('0') << (uint64_t) *ptr_l++ << (is_join ? "" : " ");
            oss_h << std::hex << std::setw(sizeof(T)*2) << std::setfill('0') << (uint64_t) *ptr_h++ << (is_join ? "" : " ");
        }
        return oss_l.str() + " .. " + oss_h.str();
    }
}

template<typename T, typename T2, int unsigned M, int unsigned N>
inline static std::string static2DArrayPrt(const T* array, bool dumpAll = false) {
    static_assert(sizeof(T) == N*sizeof(T2));
    if ( dumpAll == true || (M*N) <= MAX_DUMP_HALF_LIMIT || MAX_DUMP_HALF_LIMIT == 0 ) {
        std::ostringstream oss;
        const T2* ptr = (T2*) array;
        for(int unsigned i=0; i<(M*N); i++) {
            bool is_join = ( i%N == 0 || i+1 == (M*N) );
            oss << std::hex << std::setw(sizeof(T2)*2/N) << std::setfill('0') << (uint64_t) *ptr++ << (is_join ? "" : " ");
        }
        return oss.str();
    } else {
        std::ostringstream oss_l;
        std::ostringstream oss_h;
        const T2* ptr_l = (uint64_t*) array;
        const T2* ptr_h = (uint64_t*) array + (M*N) - N*MAX_DUMP_HALF_LIMIT;
        for(int unsigned i=0; i<N*MAX_DUMP_HALF_LIMIT; i++) {
            bool is_join = ( i%N == 0 || i+1 == N*MAX_DUMP_HALF_LIMIT );
            oss_l << std::hex << std::setw(sizeof(T2)*2/N) << std::setfill('0') << (uint64_t) *ptr_l++ << (is_join ? "" : " ");
            oss_h << std::hex << std::setw(sizeof(T2)*2/N) << std::setfill('0') << (uint64_t) *ptr_h++ << (is_join ? "" : " ");
        }
        return oss_l.str() + " .. " + oss_h.str();
    }
}

template<typename T, int unsigned M>
inline static std::string structArrayPrt(const T* array, const char *name, bool dumpAll = false) {
    if ( dumpAll == true || M <= (2*MAX_DUMP_HALF_LIMIT) || MAX_DUMP_HALF_LIMIT == 0 ) {
        std::ostringstream oss;
        int unsigned index = 0;
        for(int unsigned i=0; i<M; i++) {
            bool is_last = ( i+1 == M );
            oss << name << "[" << index << "]<" << array[index].prt(dumpAll) << ">" << (is_last ? "" : " "); index++;
        }
        return oss.str();
    } else {
        std::ostringstream oss_l;
        std::ostringstream oss_h;
        int unsigned index_l = 0;
        int unsigned index_h = M - MAX_DUMP_HALF_LIMIT;
        for(int unsigned i=0; i<MAX_DUMP_HALF_LIMIT; i++) {
            bool is_last = ( i+1 == MAX_DUMP_HALF_LIMIT );
            oss_l << name << "[" << index_l << "]<" << array[index_l].prt(dumpAll) << ">" << (is_last ? "" : " "); index_l++;
            oss_h << name << "[" << index_h << "]<" << array[index_h].prt(dumpAll) << ">" << (is_last ? "" : " "); index_h++;
        }
        return oss_l.str() + " .. " + oss_h.str();
    }
}

// from boost usage example
class spinlock {
private:
    std::atomic_flag flag_ = ATOMIC_FLAG_INIT;

public:
    void lock() {
        while (flag_.test_and_set(std::memory_order_acquire)) {
            /* busy-wait */
        }
    }

    void unlock() {
        flag_.clear(std::memory_order_release);
    }
};

// actual class that does the work
class logging {
public:
    static logging &GetInstance() {
        static std::mutex m_mutex;
        std::lock_guard<std::mutex> lock(m_mutex);
        static logging instance;
        return instance;
    }
    uint64_t startTime = 0;
    void logPrint(const std::string &fname, const std::string &block, const std::string &logmsg, const loglevel_e loglevel=LOG_NORMAL);
    void addBlock(const std::string block, const verbosity_e verbosity);
    verbosity_e blockVerbosity(const std::string block);
    void logPrintDirect(const std::string &logmsg);
    void logDirect(const std::string &logmsg, const loglevel_e loglevel=LOG_NORMAL);
    verbosity_e verbosityDecode(const std::string &verbosityStr);
    void bufferDump(uint8_t *buff, int size);
    // to register a status function, put this in your constructor and add statusPrint() function in your class
    // logging::GetInstance().registerStatus([this](){ statusPrint();});
    void registerStatus(std::string name_, std::function<void(void)> funct)
    {
        if (name_ == "" || funct == nullptr)
        {
            Q_ASSERT_CTX(false, name_, "registerStatus: name or function is null");
        }
        statusList.push_back(std::pair<std::string, std::function<void(void)> >(name_, funct));
    };
    void registerInterfaceStatus(std::string name_, std::function<void(void)> funct)
    {
        if (name_ == "" || funct == nullptr)
        {
            Q_ASSERT_CTX(false, name_, "registerStatus: name or function is null");
        }
        interfaceStatusList.push_back((std::pair<std::string, std::function<void(void)> >(name_, funct)));
    };
    void registerLockStatus(std::string name_, std::function<void(void)> funct)
    {
        if (name_ == "" || funct == nullptr)
        {
            Q_ASSERT_CTX(false, name_, "registerStatus: name or function is null");
        }
        lockStatusList.push_back((std::pair<std::string, std::function<void(void)> >(name_, funct)));
    };
    void registerQueueStatus(std::string name_, std::function<void(void)> funct)
    {
        if (name_ == "" || funct == nullptr)
        {
            Q_ASSERT_CTX(false, name_, "registerStatus: name or function is null");
        }
        queueStatusList.push_back((std::pair<std::string, std::function<void(void)> >(name_, funct)));
    };
    // to allow collection of statistics at end of run
    void registerReport(std::string name_, std::function<std::string(void)> funct)
    {
        if (name_ == "" || funct == nullptr)
        {
            Q_ASSERT_CTX(false, name_, "registerStatus: name or function is null");
        }
        reportList.push_back((std::pair<std::string, std::function<std::string(void)> >(name_, funct)));
    };
    void statusPrint(void);
    void queueStatusPrint(void);
    void trackerDump(void);
    void final(void);
    void interfaceStatus(void);
    void lockStatus(void);
    std::string report(void);
    void setDefaultVerbosity(verbosity_e verbosity) { defaultVerbosity = verbosity; };
    verbosity_e getDefaultVerbosity(void) { return(defaultVerbosity); };
    void setAddressValuePrint(bool enable) { enableAddresses = enable; };
    void setTimeStampPrint(bool enable) { enableTimeStamp = enable; };
    void disableLogging(void) { disableLogging_ = true; };
    void enableLogging(void) { disableLogging_ = false; };
    std::string getAddressString(uint64_t address)
    {
        std::stringstream ss;

        if (enableAddresses)
        {
            ss << "0x" << std::setfill('0') << std::setw(16) << std::hex << address;
            return ss.str();
        }
        else
        {
            return "ADDRHIDDEN";
        }
    }
    inline std::string logLevelToString(const loglevel_e loglevel)
    {
        switch (loglevel)
        {
            case LOG_ALWAYS:
                return "ALWAYS";
                break;
            case LOG_IMPORTANT:
                return "IMPORTANT";
                break;
            case LOG_NORMAL:
                return "NORMAL";
                break;
            case LOG_DEBUG:
                return "DEBUG";
                break;
            default:
                return "UNKNOWN";
        };
    }
private:
    logging()
    {
        struct timespec ts;

        clock_gettime(CLOCK_MONOTONIC, &ts);
        // Successfully obtained the time
        startTime = ts.tv_sec * 1000000LL + ts.tv_nsec / 1000LL;

    }; //singleton pattern
    std::unordered_map<std::string, verbosity_e> dontLogBlockMap;
    spinlock lockOut;
    std::vector<std::pair<std::string, std::function<void(void)> > > statusList;
    std::vector<std::pair<std::string, std::function<void(void)> > > interfaceStatusList;
    std::vector<std::pair<std::string, std::function<void(void)> > > lockStatusList;
    std::vector<std::pair<std::string, std::function<void(void)> > > queueStatusList;
    std::vector<std::pair<std::string, std::function<std::string(void)> > > reportList;
    verbosity_e defaultVerbosity = VERBOSITY_LOW;
    bool enableAddresses = false;
    bool enableTimeStamp = false;
    bool disableLogging_ = false;
};

// utility class to contain block specific logging info
class logBlock {
private:
    logging &log_;
    verbosity_e verbosity_;
    const std::string block_;
    std::string prefix_;
public:
    logBlock(const std::string prefix, const std::string block)
      : log_(logging::GetInstance()),
        block_(block),
        prefix_(block + "." + prefix + ":")
    {
        verbosity_ = log_.blockVerbosity(block_); //for ordering reasons perform in the body
    };
    logBlock(const std::string block)
      : log_(logging::GetInstance()),
        block_(block),
        prefix_(block + ":")
    {
        verbosity_ = log_.blockVerbosity(block_); //for ordering reasons perform in the body
    };
    void setLogPrefix(const std::string prefix) {prefix_ = prefix; };
    std::string getLogPrefix(void) { return prefix_; }
    void setVerbosity(verbosity_e verbosity) {verbosity_ = verbosity; };
    inline bool isMatch(const loglevel_e logLevel)
    {
        return ((int)logLevel <= (int)verbosity_);
    }
    inline void logPrint(const std::string &logmsg, const loglevel_e logLevel=LOG_NORMAL)
    {
        // if this message is at the same or higher level than our current logging threshold for this block then log
        if (isMatch(logLevel))
        {
            log_.logPrintDirect(prefix_ + logmsg);
        };
    }
    template <typename stringFunct, typename = std::enable_if_t<std::is_invocable_r_v<std::string, stringFunct>>>
    inline void logPrint(stringFunct&& messageFunct, const loglevel_e logLevel=LOG_NORMAL)
    {
        // if this message is at the same or higher level than our current logging threshold for this block then log
        if (isMatch(logLevel))
        {
            log_.logPrintDirect(prefix_ + messageFunct());
        };
    }
};

class errorCode {
public:
    static void pass(bool force=false)
    {
        int &errorCode = getErrorCode();
        if (errorCode <= 0 || force)
        {
            errorCode = 0;
            getString() = "No error";
        }
    }
    static void fail(const std::string errorString, const int errorCode=1)
    {
        getErrorCode() = errorCode;
        getString() = errorString;
    }
    static int getExitCode(void)
    {
        return getErrorCode();
    }
    static std::string getErrorString(void)
    {
        return getString();
    }
    static void setErrorString(std::string s)
    {
        getString() = s;
    }
private:
    static std::string & getString()
    {
        static std::string errorString = "Unknown error";
        return errorString;
    }
    static int & getErrorCode()
    {
        static int error = -1;
        return error;
    }
};

#endif //LOGGING_H
