#ifndef SYNCH_LOCK_H
#define SYNCH_LOCK_H
#ifdef A2CPRO
#include "synchLockPro.h"
#else
#include "systemc.h"
#include <string>
#include <map>
#include <boost/lockfree/spsc_queue.hpp>
#include <format>
#include "logging.h"
#include <type_traits>
#include "instanceFactory.h"
#include <queue>

extern std::string systemC_safe_string(const std::string &str);

// synchLock allows replication of arbitration decisions between to implementations of the same block
// in single implementation mode, the synchLock is a simple mutex
// if two implementations are running in parallel, then the synchLock make one of the implementations wait
// until the other implementation has completed its arbitration decision and forces the second implementation to follow
template <class T = uint64_t>
class synchLock
{
public:
    synchLock(const std::string hierarchicalName_, const std::string lockName_, bool producer_) :
        smartMuxex((systemC_safe_string(hierarchicalName_) + "_" + lockName_ ).c_str()),
        hierarchicalName(hierarchicalName_),
        lockName(hierarchicalName_ + "_" + lockName_ )
    { };
    void lockStatus(void) {}
    void synch(T syncValue, std::string threadName) {}
    void push(T syncValue, std::string threadName) {}
    void reset(std::string threadName) {}
    void lock(T syncValue)
    {
        smartMuxex.lock();
        isLocked = true;
    }
    void unlock(void)
    {
        smartMuxex.unlock();
        isLocked = false;
    }
    T arb(T syncValue) { return syncValue; }
    void setEvent(std::shared_ptr<sc_event> event) {}
    void setPrt(std::function<std::string(const T &value)> prt_, bool recursion = true) {}
    std::string name()
    {
        return lockName;
    }
private:
    sc_mutex smartMuxex;
    std::string hierarchicalName;
    std::string lockName;
    bool isLocked = false;
};

struct arraySynchRecord
{
public:
    uint64_t magicNumber;
    uint64_t value;

    std::ostream& operator << (std::ostream &os) {
        os << "magicNumber:" << magicNumber << " value:0x" << std::hex << value;
        return os;
    }
    friend std::ostream& operator<<(std::ostream &os, const arraySynchRecord &record) {
        os << "magicNumber:" << record.magicNumber << " value:0x" << std::hex << record.value;
        return os;
    }
    bool operator == (const arraySynchRecord &rhs) {
        return (magicNumber == rhs.magicNumber && value == rhs.value);
    }
    bool operator != (const arraySynchRecord &rhs) {
        return !(*this == rhs);
    }
    std::string prt(void) {
        std::stringstream ss;
        ss << "magicNumber:" << magicNumber << " value:0x" << std::hex << value;
        return ss.str();
    }
};

class synchLockFactoryBase
{
public:
    virtual ~synchLockFactoryBase() = default;
    virtual std::string dumpInstanceLocks(std::string hierarchicalName) = 0;
};

class synchLockFactoryRegistery
{
public:
    static synchLockFactoryRegistery& getInstance()
    {
        static synchLockFactoryRegistery instance;
        return instance;
    }
    void registerSynchLockFactory(synchLockFactoryBase *factory)
    {
        factories.push_back(factory);
    }
    // for platforms that create a hierarchy of instances with a prefix (eg VCS puts sc_main. in front of all instances)
    // set this before creating any instances
    void setHierarchyPrefix(const std::string prefix)
    {
        hierarchyPrefix = prefix;
    }
    std::string dumpInstanceLocks(std::string hierarchicalName)
    {
        std::stringstream ss;
        for (auto &factory : factories)
        {
            ss << factory->dumpInstanceLocks(hierarchicalName);
        }
        return ss.str();
    }
    std::string getHierarchyPrefix(void)
    {
        return hierarchyPrefix;
    }
private:
    std::vector<synchLockFactoryBase *> factories;
    synchLockFactoryRegistery() {}
    void operator=(synchLockFactoryRegistery const&);
    synchLockFactoryRegistery(synchLockFactoryRegistery const&);
    std::string hierarchyPrefix = "";
};



template< class T = uint64_t >
class synchLockFactory : public synchLockFactoryBase
{
public:
    static synchLockFactory<T>& getInstance()
    {
        static synchLockFactory<T> instance;
        return instance;
    }
    std::shared_ptr<synchLock<T>> newLock(const char * hierarchicalName, const char * lockName)
    {
        return newLock(std::string(hierarchicalName), std::string(lockName));
    }
    std::shared_ptr<synchLock<T>> newLock(const std::string hierarchicalName, const std::string lockName)
    {
        std::string lockKey = hierarchicalName + "_" + lockName;
        auto it = locks.find(lockKey);
        bool found;
        found = (it != locks.end()); // first block is the producer
        auto lock = std::make_shared<synchLock<T>>(hierarchicalName.c_str(), lockName, !found);
        // set a default prt function for non-integers, can be overridden by the user
        if constexpr (!std::is_integral_v<T>) {
            lock->setPrt([](T value) -> std::string {
                return value.prt();
            });
        }
        if (found)
        {
            Q_ASSERT_CTX_NODUMP(false,"synchLockFactory", "Tandem mode not support");
        } else {
            // store it in the map.
            locks[lockKey] = lock;
        }
        return lock;
    }
    // allow hw wrappers to register lock usage
    void registerLock(const char * hierarchicalName, const char * lockName)
    {
        (void) newLock(hierarchicalName, lockName); // throw away the result
    }
    void registerLock(std::string hierarchicalName, std::string lockName)
    {
        (void) newLock(hierarchicalName, lockName); // throw away the result
    }
    std::string dumpInstanceLocks(std::string hierarchicalName)
    {
        std::stringstream ss;
        for (auto &lock : locks)
        {
            if (lock.first.find(hierarchicalName) != std::string::npos)
            {
                ss << lock.first << '\n';
            }
        }
        return ss.str();
    }
private:
    std::unordered_map<std::string, std::shared_ptr<synchLock<T>>> locks;
    synchLockFactory<T>()
    {
        synchLockFactoryRegistery::getInstance().registerSynchLockFactory(this);
        hierarchyPrefixLen = (synchLockFactoryRegistery::getInstance().getHierarchyPrefix()).length();
        if (hierarchyPrefixLen > 0) {
            hierarchyPrefixLen++; // add one for the dot
        }
    }
    void operator=(synchLockFactory<T> const&);
    synchLockFactory<T>(synchLockFactory<T> const&);
    logging &log = logging::GetInstance();
    int hierarchyPrefixLen = 0;

public:
    std::string getInstanceName(const char * hierarchicalName, const char * lockName)
    {
        static std::vector<std::pair<std::string, std::string>> nameMappings;
        for (auto &nameMapping : nameMappings)
        {
            if (nameMapping.first == hierarchicalName) {
                return nameMapping.second + "_" + lockName;
            }
        }
        std::string lookupStr(hierarchicalName);
        if (hierarchyPrefixLen > 0) {
            lookupStr = lookupStr.substr(hierarchyPrefixLen);
        }
        std::string newName = instanceFactory::getHierarchyName(lookupStr, BLOCKBASEMODE_NORMAL);
        nameMappings.push_back(std::make_pair(hierarchicalName, newName));
        return newName + "_" + lockName;
    }

    void lockByKey (const char* hierarchy, const char* lockKey, const char* threadName, T syncValue) { }
    void unlockByKey (const char* hierarchy, const char* lockKey, const char* threadName) {}
    void pushByKey (const char* hierarchy, const char* lockKey, const char* threadName, T syncValue) {}
    inline bool isTandemMode(void) { return false; }
    void arbByKey(const char* hierarchy, const char* lockKey, T syncValue) {
    }
};


// creates an array of locks similar to hwMemory to allow for multiple locks to be created and synchronized with single synchLock
class synchArrayLock
{
public:
    synchArrayLock(const std::string name_, const std::string arrayName_, uint64_t rows_, std::function<std::string(const arraySynchRecord &value)> prt_ = nullptr) :
        m_name(name_ + "_" + arrayName_),
        m_mutexes(rows_, false),
        m_event((systemC_safe_string(m_name) + "_event").c_str()),
        m_mutex((systemC_safe_string(m_name) + "_mutex").c_str())
    {    }
    void lock(uint64_t row, uint64_t magicNumber)
    {
        bool locked = false;

        while (!locked)
        {
            m_mutex.lock();
            if (!m_mutexes[row]) {
                m_mutexes[row] = true;
                locked = true;
                m_mutex.unlock();
            } else {
                m_mutex.unlock();
                wait(m_event);
            }
        }
    }
    void unlock(uint64_t row)
    {
        m_mutexes[row] = false;
        m_event.notify();
    }
    bool isLocked(uint64_t row)
    {
        return m_mutexes[row];
    }
private:
    void statusPrint(void) {

    }
    std::string m_name;
    std::vector<bool> m_mutexes;

    sc_event m_event;
    sc_mutex m_mutex;


};


// must match DPI function prototypes
extern "C" {
    extern int is_tandem();
    extern void mutex_lock(const char* hierarchy, const char* name, const char* thread_name, long long value);
    extern void mutex_unlock(const char* hierarchy, const char* name, const char* thread_name);
    extern void synch_lock_arb(const char* hierarchy, const char* name, long long value);
    extern void row_lock(const char* hierarchy, const char* name, const char* thread_name, long long magicNumber, long long row);
    extern void push_arb(const char* hierarchy, const char* name, const char* thread_name, long long value);
}


extern uint32_t fnv1a_hash(const uint8_t* data, size_t length);
#endif //A2CPRO
#endif //SYNCH_LOCK_H
