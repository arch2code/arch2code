// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include "logging.h"
#include <iostream>
#include <iomanip>
#include "tracker.h"
#include "systemc.h"
#include <time.h>

void log(const std::string &fname, std::string &block, const std::string &logmsg, const loglevel_e loglevel)
{
    static logging &log = logging::GetInstance();
    log.logPrint(fname, block, logmsg, loglevel);
}
void logDirect(const std::string &logmsg, const loglevel_e loglevel)
{
    static logging &log = logging::GetInstance();
    log.logDirect(logmsg, loglevel);
}

void logging::logDirect(const std::string &logmsg, const loglevel_e loglevel)
{
    if ((disableLogging_ == false) && ((int)defaultVerbosity >= (int)loglevel ))
    {
        std::cout << logmsg << '\n';
    }
}

void logging::addBlock(std::string block, verbosity_e verbosity)
{
    dontLogBlockMap[block] = verbosity;
}

verbosity_e logging::blockVerbosity(const std::string block)
{
    verbosity_e tmpVerbosity;
    auto it = dontLogBlockMap.find(block);
    if ( it == dontLogBlockMap.end() )
    {
        tmpVerbosity = defaultVerbosity;  //if the block is not overridden then normal logging
    } else {
        tmpVerbosity = it->second;
    }
    return (tmpVerbosity);
}

void logging::logPrint(const std::string &fname, const std::string &block, const std::string &logmsg, const loglevel_e loglevel)
{
    auto it = dontLogBlockMap.find(block);
    bool printIt = false;
    if ( it == dontLogBlockMap.end() )
    {
        // no exceptions for this block so just check against default
        if ( (int)defaultVerbosity >= (int)loglevel )
        {
            printIt = true;
        }
    } else {
        // block has an exception so check against that
        if ( (int)it->second >= (int)loglevel )
        {
            printIt = true;
        }
    }
    if ( printIt && (disableLogging_ == false) )
    {
        std::string timeStamp = "";
        if (enableTimeStamp)
        {
            struct timespec ts;

            clock_gettime(CLOCK_MONOTONIC, &ts);
            // Successfully obtained the time
            uint64_t useconds = (ts.tv_sec * 1000000LL + ts.tv_nsec / 1000LL) - startTime;
            sc_time current_time = sc_time_stamp();
            //timeStamp = std::format("{d} {} ",useconds, current_time );
        }
        std::cout << timeStamp << fname << logmsg;
    }

}

void logging::logPrintDirect(const std::string &logmsg)
{
    if (disableLogging_ == false)
    {
        if (enableTimeStamp)
        {
            struct timespec ts;

            clock_gettime(CLOCK_MONOTONIC, &ts);
            // Successfully obtained the time
            uint64_t useconds = (ts.tv_sec * 1000000LL + ts.tv_nsec / 1000LL) - startTime;
            sc_time current_time = sc_time_stamp();
            std::string timeStamp = std::format("{} {} ", useconds, current_time.to_string() );
            std::cout << timeStamp << logmsg << '\n';
        } else {
            std::cout << logmsg << '\n';
        }
    }
}

#define BYTES_PER_LINE 32
#define BYTES_PER_LINE_MASK (BYTES_PER_LINE-1)
#define BYTES_PER_QWORD 8
#define BYTES_PER_QWORD_LOG2 3
#define BYTES_PER_QWORD_MASK (BYTES_PER_QWORD-1)
#define QWORD_PER_LINE (BYTES_PER_LINE/BYTES_PER_QWORD)
#define QWORD_PER_LINE_MASK (QWORD_PER_LINE-1)
void logging::bufferDump(uint8_t *buff, int size)
{
    if (size < BYTES_PER_LINE) {
        for (int i=0; i<size; i++)
        {
            std::cout << std::format("{:02x} ", (uint64_t)*(buff+i));
        }
        std::cout << '\n';
        return;
    }

    int front = (BYTES_PER_LINE - (( (uint64_t)buff) & BYTES_PER_LINE_MASK)) & BYTES_PER_LINE_MASK; // bytes to process before aligned
    int back  = (size + (uint64_t)buff ) & BYTES_PER_LINE_MASK;        // bytes to process after aligned
    int middle = size - front - back;                // aligned data
    int line = 0;
    lockOut.lock();
    uint8_t * current = buff;
    if (front > 0)
    {
        std::string s;
        int qWordAlignment = (front) >> BYTES_PER_QWORD_LOG2;
        for(int i=0; i<((BYTES_PER_LINE-front) >> BYTES_PER_QWORD_LOG2); i++)
        {
            s = s + " ................";
        }
        int byteAlignment = front & BYTES_PER_QWORD_MASK;
        if (byteAlignment > 0)
        {
            for(int i=0; i<((BYTES_PER_QWORD-byteAlignment) & BYTES_PER_QWORD_MASK); i++)
            {
                s = s + "..";
            }
            for(int i=0; i<byteAlignment; i++)
            {
                s = std::format("{:02x}", (uint64_t)*(current)) + s;
                current++;
            }
            s = " " + s;
        }
        for(int i=0; i<qWordAlignment; i++)
        {
            s = std::format(" {:016x}", *(uint64_t*)current ) + s;
            current +=8;
        }
        std::cout << std::setw(4) << line << ":" << s << '\n';
    }
    line++;
    uint64_t * qWordBuff = (uint64_t *)current;
    for(int i=0; i<(middle/BYTES_PER_LINE); i++)
    {
        std::cout << std::format("{:4d}: {:016x} {:016x} {:016x} {:016x}", line, *(qWordBuff+3), *(qWordBuff+2), *(qWordBuff+1), *(qWordBuff)) << '\n';
        qWordBuff +=4;
        line++;
    }
    if (back > 0)
    {
        std::string s;
        int bytes = back & BYTES_PER_QWORD_MASK;
        int qWords = (back >> BYTES_PER_QWORD_LOG2);
        for(int i=0; i<qWords; i++)
        {
            s = std::format(" {:016x}", *qWordBuff ) + s;
            qWordBuff++;
        }
        current = (uint8_t *)qWordBuff;
        if (bytes > 0)
        {
            for(int i=0; i<bytes; i++)
            {
                s = std::format("{:02x}", (uint64_t)*current ) + s;
                current++;
            }
            for(int i=0; i<((BYTES_PER_QWORD-bytes) & BYTES_PER_QWORD_MASK); i++)
            {
                s = ".." + s;
            }
            s = " " + s;
        }
        for(int i=0; i<((BYTES_PER_LINE-back) >> BYTES_PER_QWORD_LOG2); i++)
        {
            s = " ................" + s;
        }
        std::cout << std::setw(4) << line << ":" << s << '\n';
    }
    lockOut.unlock();

}

void logging::statusPrint(void)
{
    std::string prev("");
    for( auto & status : statusList)
    {
        if ( status.second != nullptr ) {
            status.second();
        } else {
            logDirect(std::format("statusPrint: {} is null, prev {}", status.first , prev), LOG_IMPORTANT);
            Q_ASSERT_CTX_NODUMP(false, "", "statusPrint: null status");
        }
        prev = status.first;
    }
    interfaceStatus();
    lockStatus();
}
void logging::queueStatusPrint(void)
{
    for( auto & status : queueStatusList)
    {
        if ( status.second != nullptr ) {
            status.second();
        } else {
            logDirect(std::format("queueStatusList: {} is null", status.first), LOG_IMPORTANT);
            Q_ASSERT_CTX_NODUMP(false, "", "queueStatusList: null status");
        }
    }
}
void logging::trackerDump(void)
{
    trackerCollection::GetInstance().dump();
}
void logging::final(void)
{
    statusPrint();
    trackerDump();
}
std::string logging::report(void)
{
    std::string ret;
    for( auto & report : reportList)
    {
        if ( report.second != nullptr ) {
            ret += report.second();
        } else {
           logDirect(std::format("report: {} is null", report.first), LOG_IMPORTANT);
           Q_ASSERT_CTX_NODUMP(false, "", "report: null status");
        }
    }
    return ret;
}
void logging::interfaceStatus(void)
{
    logDirect("Begin Interface status dump:", LOG_IMPORTANT);
    for( auto & status : interfaceStatusList)
    {
        if ( status.second != nullptr ) {
            status.second();
        } else {
           logDirect(std::format("interfaceStatus: {} is null", status.first), LOG_IMPORTANT);
           Q_ASSERT_CTX_NODUMP(false, "", "interfaceStatus: null status");
        }
    }
    logDirect("End Interface status dump:", LOG_IMPORTANT);

}
void logging::lockStatus(void)
{
    logDirect("Begin lock status dump:", LOG_IMPORTANT);
    for( auto & status : lockStatusList)
    {
        if ( status.second != nullptr ) {
            status.second();
        } else {
           logDirect(std::format("lockStatus: {} is null", status.first), LOG_IMPORTANT);
            Q_ASSERT_CTX_NODUMP(false, "", "lockStatus: null status");
        }
    }
    logDirect("End lock status dump:", LOG_IMPORTANT);

}

verbosity_e logging::verbosityDecode(const std::string &VerbosityStr)
{
    std::string lowercaseVerbosity = VerbosityStr;
    std::transform(lowercaseVerbosity.begin(), lowercaseVerbosity.end(), lowercaseVerbosity.begin(), ::tolower);

    // Define a mapping of Verb level text to integer values
    std::unordered_map<std::string, verbosity_e> VerbosityMap = {
        {"low", VERBOSITY_LOW},
        {"0",VERBOSITY_LOW},
        {"med", VERBOSITY_MEDIUM},
        {"medium", VERBOSITY_MEDIUM},
        {"1", VERBOSITY_MEDIUM},
        {"high", VERBOSITY_HIGH},
        {"2", VERBOSITY_HIGH},
        {"full", VERBOSITY_FULL},
        {"3", VERBOSITY_FULL}
    };
    // Look up the Verb level in the map
    auto it = VerbosityMap.find(lowercaseVerbosity);
    if (it != VerbosityMap.end()) {
        // Return the corresponding integer value
        return it->second;
    } else {
        // If the text does not match any known Verb levels, return a default value
        return VERBOSITY_UNKNOWN;
    }
}
