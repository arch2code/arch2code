
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
// GENERATED_CODE_PARAM --context=axiStd.yaml
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
package axiStd_package;

// types
typedef logic[4-1:0] _axiIdT; //Type for axi ID tags. Used for ARID, RID, AWID, BID.
typedef logic[8-1:0] _axiLenT; //Exact number of transfers in a burst.
typedef logic[3-1:0] _axiSizeT; //Bytes in transfer encoded 0=1, 1=2, 2=4, 3=8, 4=16, 5=32, 6=64, 7=128
typedef logic[3-1:0] _axiProtT; //Protection type for the AXI protocol Bit 0 - Privileged, Bit 1 - Secure, Bit 2 - Data Access
typedef logic[4-1:0] _axiQoST; //QoS type for the AXI protocol
typedef logic[4-1:0] _axiRegionT; //Region type for the AXI protocol

// enums
typedef enum logic[2-1:0] {        //Response type for the AXI protocol
    AXIRESP_OKAY = 0,        // OKAY
    AXIRESP_EXOKAY = 1,      // EXOKAY
    AXIRESP_SLVERR = 2,      // SLVERR
    AXIRESP_DECERR = 3      // DECERR
} _axiResponseT;
typedef enum logic[2-1:0] {           //The burst type and the size information determine how the address for each transfer within the burst is calculated
    AXIBURST_FIXED = 0,      // FIXED
    AXIBURST_INCR = 1,       // INCR
    AXIBURST_WRAP = 2       // WRAP
} _axiBurstT;
typedef enum logic[4-1:0] {         //Read Cache type for the AXI protocol
    AXIRDCACHE_NONBUFF = 0,  // Device Non-bufferable
    AXIRDCACHE_BUFF = 1,     // Device Bufferable
    AXIRDCACHE_NONCACHE_NONBUFF = 2, // Normal Non-cacheable Non-bufferable
    AXIRDCACHE_NONCACHE_BUFF = 3, // Normal Non-cacheable Bufferable
    AXIRDCACHE_WRTHRU_NOALLOC = 10, // Write-through No-allocate
    AXIRDCACHE_WRBACK_NOALLOC = 11, // Write-back No-allocate
    AXIRDCACHE_WRTHRU_RDALLOC = 14, // Write-through Read-allocate
    AXIRDCACHE_WRBACK_RDALLOC = 15 // Write-back Read-allocate
} _axiRdCacheT;
typedef enum logic[4-1:0] {         //Read Cache type for the AXI protocol
    AXIWRCACHE_NONBUFF = 0,  // Device Non-bufferable
    AXIWRCACHE_BUFF = 1,     // Device Bufferable
    AXIWRCACHE_NONCACHE_NONBUFF = 2, // Normal Non-cacheable Non-bufferable
    AXIWRCACHE_NONCACHE_BUFF = 3, // Normal Non-cacheable Bufferable
    AXIWRCACHE_WRTHRU_NOALLOC = 6, // Write-through No-allocate
    AXIWRCACHE_WRBACK_NOALLOC = 7, // Write-back No-allocate
    AXIWRCACHE_WRTHRU_WRALLOC = 14, // Write-through Write-allocate
    AXIWRCACHE_WRBACK_WRALLOC = 15 // Write-back Write-allocate
} _axiWrCacheT;

// structures
endpackage : axiStd_package
// GENERATED_CODE_END
