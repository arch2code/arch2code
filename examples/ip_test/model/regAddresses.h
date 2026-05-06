#ifndef REGADDRESSES_H
#define REGADDRESSES_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip_top
// GENERATED_CODE_BEGIN --template=includes --section=addresses
//instance base addresses
#define BASE_ADDR_IP_TOP_TB            0x0
#define BASE_ADDR_U_IP_TOP             0x0
#define BASE_ADDR_UCPU                 0x0
#define BASE_ADDR_UAPBDECODE           0x0
#define BASE_ADDR_USRC                 0x0
#define BASE_ADDR_UIP0                 0x0
#define BASE_ADDR_UIP1                 0x1000000
#define BASE_ADDR_UIPREGS              0x0
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=includes --section=regAddresses
//register addresses
#define REG_IP_IPCFG                        0x180
#define REG_IP_IPLASTDATA                   0x188
//memories base addresses
#define REG_IP_IPMEM                        0x0
#define REG_IP_IPFIXEDMEM                   0x80
#define REG_IP_IPNONCONSTMEM                0x100
// GENERATED_CODE_END

#endif //REGADDRESSES_H
