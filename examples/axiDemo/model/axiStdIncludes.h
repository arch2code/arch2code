
#ifndef AXISTDINCLUDES_H_
#define AXISTDINCLUDES_H_
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include <cstdint>
#include <format>
#include <iostream>
#include <iomanip>

// GENERATED_CODE_PARAM --context=axiStd.yaml
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=include_hdr

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
//constants

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
// types
typedef uint8_t _axiIdT; // [4] Type for axi ID tags. Used for ARID, RID, AWID, BID.
typedef uint8_t _axiLenT; // [8] Exact number of transfers in a burst.
typedef uint8_t _axiSizeT; // [3] Bytes in transfer encoded 0=1, 1=2, 2=4, 3=8, 4=16, 5=32, 6=64, 7=128
typedef uint8_t _axiProtT; // [3] Protection type for the AXI protocol Bit 0 - Privileged, Bit 1 - Secure, Bit 2 - Data Access
typedef uint8_t _axiQoST; // [4] QoS type for the AXI protocol
typedef uint8_t _axiRegionT; // [4] Region type for the AXI protocol

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
// enums
enum  _axiResponseT {        //Response type for the AXI protocol
    AXIRESP_OKAY=0,          // OKAY
    AXIRESP_EXOKAY=1,        // EXOKAY
    AXIRESP_SLVERR=2,        // SLVERR
    AXIRESP_DECERR=3 };      // DECERR
inline const char* _axiResponseT_prt( _axiResponseT val )
{
    switch( val )
    {
        case AXIRESP_OKAY: return( "AXIRESP_OKAY" );
        case AXIRESP_EXOKAY: return( "AXIRESP_EXOKAY" );
        case AXIRESP_SLVERR: return( "AXIRESP_SLVERR" );
        case AXIRESP_DECERR: return( "AXIRESP_DECERR" );
    }
    return("!!!BADENUM!!!");
}
enum  _axiBurstT {           //The burst type and the size information determine how the address for each transfer within the burst is calculated
    AXIBURST_FIXED=0,        // FIXED
    AXIBURST_INCR=1,         // INCR
    AXIBURST_WRAP=2 };       // WRAP
inline const char* _axiBurstT_prt( _axiBurstT val )
{
    switch( val )
    {
        case AXIBURST_FIXED: return( "AXIBURST_FIXED" );
        case AXIBURST_INCR: return( "AXIBURST_INCR" );
        case AXIBURST_WRAP: return( "AXIBURST_WRAP" );
    }
    return("!!!BADENUM!!!");
}
enum  _axiRdCacheT {         //Read Cache type for the AXI protocol
    AXIRDCACHE_NONBUFF=0,    // Device Non-bufferable
    AXIRDCACHE_BUFF=1,       // Device Bufferable
    AXIRDCACHE_NONCACHE_NONBUFF=2,   // Normal Non-cacheable Non-bufferable
    AXIRDCACHE_NONCACHE_BUFF=3,   // Normal Non-cacheable Bufferable
    AXIRDCACHE_WRTHRU_NOALLOC=10,   // Write-through No-allocate
    AXIRDCACHE_WRBACK_NOALLOC=11,   // Write-back No-allocate
    AXIRDCACHE_WRTHRU_RDALLOC=14,   // Write-through Read-allocate
    AXIRDCACHE_WRBACK_RDALLOC=15 }; // Write-back Read-allocate
inline const char* _axiRdCacheT_prt( _axiRdCacheT val )
{
    switch( val )
    {
        case AXIRDCACHE_NONBUFF: return( "AXIRDCACHE_NONBUFF" );
        case AXIRDCACHE_BUFF: return( "AXIRDCACHE_BUFF" );
        case AXIRDCACHE_NONCACHE_NONBUFF: return( "AXIRDCACHE_NONCACHE_NONBUFF" );
        case AXIRDCACHE_NONCACHE_BUFF: return( "AXIRDCACHE_NONCACHE_BUFF" );
        case AXIRDCACHE_WRTHRU_NOALLOC: return( "AXIRDCACHE_WRTHRU_NOALLOC" );
        case AXIRDCACHE_WRBACK_NOALLOC: return( "AXIRDCACHE_WRBACK_NOALLOC" );
        case AXIRDCACHE_WRTHRU_RDALLOC: return( "AXIRDCACHE_WRTHRU_RDALLOC" );
        case AXIRDCACHE_WRBACK_RDALLOC: return( "AXIRDCACHE_WRBACK_RDALLOC" );
    }
    return("!!!BADENUM!!!");
}
enum  _axiWrCacheT {         //Read Cache type for the AXI protocol
    AXIWRCACHE_NONBUFF=0,    // Device Non-bufferable
    AXIWRCACHE_BUFF=1,       // Device Bufferable
    AXIWRCACHE_NONCACHE_NONBUFF=2,   // Normal Non-cacheable Non-bufferable
    AXIWRCACHE_NONCACHE_BUFF=3,   // Normal Non-cacheable Bufferable
    AXIWRCACHE_WRTHRU_NOALLOC=6,   // Write-through No-allocate
    AXIWRCACHE_WRBACK_NOALLOC=7,   // Write-back No-allocate
    AXIWRCACHE_WRTHRU_WRALLOC=14,   // Write-through Write-allocate
    AXIWRCACHE_WRBACK_WRALLOC=15 }; // Write-back Write-allocate
inline const char* _axiWrCacheT_prt( _axiWrCacheT val )
{
    switch( val )
    {
        case AXIWRCACHE_NONBUFF: return( "AXIWRCACHE_NONBUFF" );
        case AXIWRCACHE_BUFF: return( "AXIWRCACHE_BUFF" );
        case AXIWRCACHE_NONCACHE_NONBUFF: return( "AXIWRCACHE_NONCACHE_NONBUFF" );
        case AXIWRCACHE_NONCACHE_BUFF: return( "AXIWRCACHE_NONCACHE_BUFF" );
        case AXIWRCACHE_WRTHRU_NOALLOC: return( "AXIWRCACHE_WRTHRU_NOALLOC" );
        case AXIWRCACHE_WRBACK_NOALLOC: return( "AXIWRCACHE_WRBACK_NOALLOC" );
        case AXIWRCACHE_WRTHRU_WRALLOC: return( "AXIWRCACHE_WRTHRU_WRALLOC" );
        case AXIWRCACHE_WRBACK_WRALLOC: return( "AXIWRCACHE_WRBACK_WRALLOC" );
    }
    return("!!!BADENUM!!!");
}

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures

// GENERATED_CODE_END
#endif //AXISTDINCLUDES_H_
