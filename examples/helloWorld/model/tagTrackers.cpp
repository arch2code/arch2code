
#include <vector>
#include <string>
#include <boost/assert.hpp>
#include <fmt/format.h>
#include "logging.h"
#include "tagTrackers.h"

std::string cmdIdInfo::prt(void)
{
    std::string s = fmt::format("dummy:0x{:x}", dummy );
    return(s);
}


std::string tagInfo::prt(void)
{
    const int shortDump=8;
    std::string s;
    std::string dump;
    if (cmdId != -1)
    {
        s = fmt::format("Type:{} cmdId:0x{:x}", tagType, cmdId );
    } else {
        s = "Type:" + tagType;
    }
    if (buff != nullptr)
    {
        if (buffLen < shortDump)
        {
            for(int i=0; i<shortDump; i++)
            {
                dump = fmt::format("{} {:x}", dump, *(buff+i) );
            }
            dump = " Data:[" + dump + "]";
        } else {
            dump = fmt::format(" Data:[{:x} {:x} {:x} {:x} {:x} {:x} {:x} {:x}..]", *(buff), *(buff+1), *(buff+2), *(buff+3), *(buff+4), *(buff+5), *(buff+6), *(buff+7));
        }
        s = s + dump;
    }

    return(s);
};