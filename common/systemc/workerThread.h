#ifndef WORKERTHREAD_H
#define WORKERTHREAD_H
#include "logging.h"
#include <cstdint>
#include <condition_variable>
#include <mutex>
#include <thread>
#include <fmt/format.h>
#include <map>
#include "systemc.h"
// copyright QiStor 2022
// class to abstract event handling for systemC and real threads
// for systemC usage the worker threads are full contained within the systemC object
// for real threads the worker threads are managed in main
class globals; // forward declaration
class workerEvent
{
public:
    workerEvent(std::string name_, bool isSystemCThread_) :
        isSystemCThread(isSystemCThread_),
        name(name_),
        log_(fmt::format("workerEvent{}", name_))
        {}
    void notify(const char *why);
    void wait(const char *why);
    void setSCEvent(sc_event *pSCEvent_) {pSCEvent = pSCEvent_;};
    void waitZero(void)
    {
        if (isSystemCThread) {
            sc_core::wait(SC_ZERO_TIME);
        }
    };
    void waitnsec(uint64_t nsec)
    {
        if (isSystemCThread) {
            sc_core::wait(nsec, SC_NS);
        } else {
            std::this_thread::sleep_for(std::chrono::nanoseconds(nsec));
        }
    };
    bool isSCEventValid(void) const { return pSCEvent != nullptr; }

private:
    bool isSystemCThread = false;
    std::condition_variable cv;
    std::atomic<bool> notified{false};
    std::mutex cv_mutex;
    sc_event *pSCEvent = nullptr;
    std::string name;
    logBlock log_;
};

// base class to allow worker threads to override
class workerBase
{
public:
    workerBase(std::string name_) : name(name_) {}
    virtual void doWork(void) = 0; //do the work
    virtual bool workAvailable(void) = 0; //returns true if work is available
    virtual void startupPreSimInit(void) {}; //called once at startup
    virtual void startupInit(void) {}; //called once at startup
    virtual ~workerBase() = default;
    virtual void shutdown(void) {}; //called once at shutdown
    std::string getName(void) {return name;}
    uint64_t idleCount = 0;
    uint64_t workCount = 0;
    std::shared_ptr<workerEvent> event;
private:
    std::string name;
};


class workerThread
{
public:
    workerThread(uint64_t threadNumber_, std::shared_ptr<workerEvent> threadEvent_, std::string name_);
    std::vector<std::shared_ptr<workerBase> > workers;
    std::vector<uint64_t> threadsNotIdle;
    std::shared_ptr<workerEvent> threadEvent;
    void main(void);
    void statusPrint(void);
private:
    uint64_t threadNumber;
    logBlock log_;
    std::atomic<bool> isIdle = true;
    std::atomic<uint64_t> currentThread = 0;
    std::string name;
};

class workerFactory
{
// static class to create and manage worker threads and workerEvents
public:
    static void setNumThreads(uint64_t numThreads, bool isSystemCThread_=false) {getNumThreads() = numThreads; getSystemCThread() = isSystemCThread_;};
    // note that worker can be a nullptr in the systemC case since we will never start threads
    static void addWorker(std::string name, std::shared_ptr<workerBase> worker)
    {
        std::map<std::string, std::shared_ptr<workerBase>> & workerMap = getWorker();
        auto it = workerMap.find(name);
        if (it != workerMap.end())
        {
            Q_ASSERT_CTX_NODUMP(false, name, "Attempted to add a worker thread that already exists" );
            return;
        }
        workerMap.emplace(name, worker);
        // for systemC case we will never start threads so we should create events here
        if (isSystemCThread())
        {
            // create one event per worker and initilaize the workerEvent pointer
            std::map<std::string, std::shared_ptr<workerEvent>> & eventMap = getEventMap();
            auto event = std::make_shared<workerEvent>(name, true);
            eventMap.emplace(name, event);
        }
    }
    static void addWorker(const std::initializer_list<std::pair<std::string, std::shared_ptr<workerBase> > > & workers)
    {
        for (auto worker : workers)
        {
            addWorker(worker.first, worker.second);
        }
    }

    // this function will be used to initialse the modules even pointer
    static std::shared_ptr<workerEvent> getWorkerEvent(std::string name)
    {
        std::map<std::string, std::shared_ptr<workerEvent>> & eventMap = getEventMap();
        auto it = eventMap.find(name);
        if (it != eventMap.end())
        {
            return it->second;
        } else {
            Q_ASSERT_CTX_NODUMP(false, name, "Attempted to get an event that does not exist" );
            return nullptr;
        }
    }
    static void assignWorkersToThreads(void)
    {
        std::map<std::string, std::shared_ptr<workerBase>> & workerMap = getWorker();
        std::vector<std::shared_ptr<workerThread>> & threads = getWorkerThreads();
        std::map<std::string, std::shared_ptr<workerEvent>> & eventMap = getEventMap();
        std::vector<std::shared_ptr<workerEvent>> events;
        uint64_t &numThreads = getNumThreads();
        if (isSystemCThread())
        {
            numThreads = workerMap.size(); // override the number of threads for systemC mode
            int i=0;
            for(auto it : workerMap)
            {
                events.push_back(std::make_shared<workerEvent>(it.first + "Event" , true));
                threads.push_back(std::make_shared<workerThread>(i, events[i], it.first));
                threads[i]->workers.push_back(it.second); // assign the worker to a thread
                it.second->event = events[i];   // match up the event with the worker
                eventMap[it.first] = events[i]; // add the event to the event map
                i++;
            }
        } else {
            // create threads
            for (uint64_t i = 0; i < numThreads; i++)
            {
                std::stringstream oss;
                oss << "thread:" << i;
                std::string name = oss.str();
                events.push_back(std::make_shared<workerEvent>(name , false));
                threads.push_back(std::make_shared<workerThread>(i, events[i], name));
            }
            // assign work to threads
            int task = 0;
            for(auto it : workerMap)
            {
                threads[task]->workers.push_back(it.second); // assign the worker to a thread
                it.second->event = events[task];   // match up the event with the worker
                eventMap[it.first] = events[task]; // add the event to the event map
                task++;
                task = task % numThreads;
            }
        }

    }
    static void startCPUThreads(void)
    {
        if (isSystemCThread()) return;

        std::vector<std::shared_ptr<workerThread>> & threads = getWorkerThreads();
        std::vector<std::shared_ptr<std::thread>> & cpuThreads = getCPUThreads();
        uint64_t numThreads = getNumThreads();
        // start threads
        for (uint64_t i = 0; i < numThreads; i++)
        {
            cpuThreads.push_back(std::make_shared<std::thread>(&workerThread::main, threads[i]));
        }
    }
    static void startSystemCThread(std::string name, sc_event *event)
    {
        if (!isSystemCThread()) return;

        std::map<std::string, std::shared_ptr<workerBase>> & workerMap = getWorker();
        std::vector<std::shared_ptr<workerThread>> & threads = getWorkerThreads();
        int i = 0;
        for(auto it : workerMap)
        {
            if (it.first == name)
            {
                threads[i]->threadEvent->setSCEvent(event);
                //wait(SC_ZERO_TIME);
                threads[i]->main();
                break;
            }
            i++;
            Q_ASSERT_CTX(i < (int)threads.size(), name, "bad thread name not found");
        }
    }
    static void joinCPUThreads(void)
    {
        if (isSystemCThread()) return;

        std::vector<std::shared_ptr<std::thread>> & cpuThreads = getCPUThreads();
        uint64_t numThreads = getNumThreads();
        cout << "Joining " << numThreads << " threads" << endl;
        notifyAll();
        // join threads
        for (uint64_t i = 0; i < numThreads; i++)
        {
            cpuThreads[i]->join();
        }
    }
    static bool isSystemCThread(void) {return getSystemCThread();}
    static void notifyAll(void)
    {
        cout << "notifyAll called" << endl;
        if (isSystemCThread())
        {
            std::map<std::string, std::shared_ptr<workerEvent>> & eventMap = getEventMap();
            for(auto it : eventMap)
            {
                Q_ASSERT_CTX_NODUMP(it.second->isSCEventValid(), it.first, "SystemC event not set, is startSystemCThread() called in environment ?");
                it.second->notify("workerFactory::notifyAll");
            }
        } else {
            std::vector<std::shared_ptr<workerThread>> & threads = getWorkerThreads();
            for(auto thread : threads)
            {
                thread->threadEvent->notify("workerFactory::notifyAll");
            }
        }
    }

private:

    static uint64_t & getNumThreads(void)
    {
        static uint64_t numThreads = 0;
        return numThreads;
    }
    static std::map<std::string, std::shared_ptr<workerBase>> & getWorker(void)
    {
        static std::map<std::string, std::shared_ptr<workerBase>> map;
        return map;
    }
    static std::vector<std::shared_ptr<workerThread>> & getWorkerThreads(void)
    {
        static std::vector<std::shared_ptr<workerThread>> threads;
        return threads;
    }
    static std::vector<std::shared_ptr<std::thread>> & getCPUThreads(void)
    {
        static std::vector<std::shared_ptr<std::thread>> cpuThreads;
        return cpuThreads;
    }
    static std::map<std::string, std::shared_ptr<workerEvent>> & getEventMap(void)
    {
        static std::map<std::string, std::shared_ptr<workerEvent>> map;
        return map;
    }
    static bool & getSystemCThread(void)
    {
        static bool isSystemCThread = false;
        return isSystemCThread;
    }
};
#endif //WORKERTHREAD_H
