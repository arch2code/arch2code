// copyright QiStor 2022
#include <string>
#include <chrono>
#include <thread>
#include "logging.h"
#include "workerThread.h"
#include "endOfTest.h"
#include <fmt/format.h>
#include "simController.h"

//#define EVENTDEBUG
void workerEvent::notify(const char *why)
{
    #ifdef EVENTDEBUG
    log_.logPrint(std::string(why) );
    #endif
    if (isSystemCThread)
    {
        pSCEvent->notify();
    } else {
        std::unique_lock<std::mutex> lk(cv_mutex);
        notified.store(true, std::memory_order_release);
        cv.notify_one();
    }
}

void workerEvent::wait(const char *why)
{
    #ifdef EVENTDEBUG
    log_.logPrint(std::string(why) );
    #endif
    if (isSystemCThread)
    {
        sc_core::wait(*pSCEvent);
    } else {
        std::unique_lock<std::mutex> lk(cv_mutex);
        while (!notified.load(std::memory_order_acquire)) {
            cv.wait(lk);
        }
        notified.store(false, std::memory_order_release);
    }
}

workerThread::workerThread(uint64_t threadNumber_, std::shared_ptr<workerEvent> threadEvent_, std::string name_) :
        threadEvent(threadEvent_),
        threadNumber(threadNumber_),
        log_(fmt::format("workerThread{}", threadNumber_)),
        name(name_)
        {}


void workerThread::main(void)
{
    endOfTestState &eot = endOfTestState::GetInstance();
    for(auto & worker : workers ) {
        log_.logPrint(fmt::format("Thread {} {} hosting {} task ", threadNumber, name, worker->getName() ));
        worker->startupPreSimInit(); // perform any pre simulation init
    }
    simController::advanceStartupPhase(fmt::format("Thread {} presim ", threadNumber));

    while (simController::getStartupPhase() < STARTUP_SIMSTART) {
        threadEvent->wait(fmt::format("Thread:{} STARTUP_SIMSTART", threadNumber).c_str());
    }

    for(auto & worker : workers ) {
        worker->startupInit(); // perform any init
    }
    threadsNotIdle.resize(workers.size() + 1);
    uint64_t totalLoops = 0;

    simController::advanceStartupPhase(fmt::format("Thread {} {} startupInit ", threadNumber, name));
    while (simController::getStartupPhase() < STARTUP_DONE)
    {
        threadEvent->wait(fmt::format("Thread:{} STARTUP_DONE", threadNumber).c_str());
    }
    logging::GetInstance().registerStatus(fmt::format("Thread{}", threadNumber), [this](void){ statusPrint();});
    bool running = true;
    bool didWork = false;
    std::string idleMsg = fmt::format("ThreadIdle:{}", threadNumber);
    std::string waitMsg = fmt::format("Thread:{}Wait", threadNumber);
    while (running)
    {
        int threadsNotIdleCount = 0;
        totalLoops++;
        int id = 0;
        for(auto & worker : workers ) {
            if (worker->workAvailable()) {
                log_.logPrint([&]() { return fmt::format("Thread {} worker {} workAvailable", threadNumber, worker->getName() ); }, LOG_DEBUG);
                currentThread.store(id, std::memory_order_release);
                isIdle.store(false, std::memory_order_release);
                worker->workCount++;
                threadsNotIdleCount++;
                worker->doWork();
                isIdle.store(true, std::memory_order_release);
                didWork = true;
            } else {
                worker->idleCount++;
            }
            id++;
        }
        threadsNotIdle[threadsNotIdleCount]++;
        if (eot.isEndOfTest()) {
            running = false;
        } else {
            if (didWork) {
                threadEvent->waitZero();
                didWork = false;
            } else {
                log_.logPrint(idleMsg, LOG_DEBUG);
                threadEvent->wait(waitMsg.c_str());
            }
        }
    }

    if (threadNumber == 0) {
        log_.logPrint("\n-------- SHUTDOWN --------\n");
    }
    for(auto & worker : workers ) {
        worker->shutdown(); // perform any shutdown actions
    }
    log_.logPrint(fmt::format("Thread {} {} exiting", threadNumber, name));
    log_.logPrint(fmt::format("Thread {} total loops {}, Idle = {:f}", threadNumber, totalLoops, ((float)threadsNotIdle[0] * 100.0/totalLoops)), LOG_IMPORTANT);
    for(uint64_t i = 1; i <= workers.size(); i++) {
        log_.logPrint(fmt::format("Contention {} thread: {:f}", i, ((float)threadsNotIdle[i] * 100/totalLoops)), LOG_IMPORTANT);
    }
    for(uint64_t i = 0; i < workers.size(); i++) {
        log_.logPrint(fmt::format("Thread {} {} work = {:f} idle = {:f}", threadNumber, workers[i]->getName(), ((float)workers[i]->workCount * 100.0/totalLoops), ((float)workers[i]->idleCount * 100.0/totalLoops)), LOG_IMPORTANT);
    }
}

void workerThread::statusPrint(void)
{
    log_.logPrint(fmt::format("Thread {} status", threadNumber), LOG_IMPORTANT);

    if (isIdle.load(std::memory_order_acquire))
    {
        log_.logPrint(fmt::format("Thread {} is idle", threadNumber), LOG_IMPORTANT);
    } else {
        log_.logPrint(fmt::format("Thread {} is in {}", threadNumber, workers[currentThread.load(std::memory_order_acquire)]->getName()), LOG_IMPORTANT);
    }
}
