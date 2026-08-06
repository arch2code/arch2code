#include "fwlog.h"
#include "logging.h"

void fwlog(const std::string &logmsg, const loglevel_e loglevel)
{
    static logBlock log("FW");
    log.logPrint(logmsg, loglevel);
}
