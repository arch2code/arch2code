#include "blockBase.h"
#include "instanceFactory.h"


blockBase::blockBase(const char* loggingName_, const char* hierarchyName_, blockBaseMode bbMode_) : 
    log_(loggingName_),
    tandem(bbMode_ == BLOCKBASEMODE_TANDEM),
    tandemName_(instanceFactory::getHierarchyName(hierarchyName_, bbMode_)) 
{}

blockBase::blockBase(const char* loggingName_, const char* hierarchyName_) : 
    log_(loggingName_),
    tandem(false),
    tandemName_("")
{}
