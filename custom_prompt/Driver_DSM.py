SYS_PROMPT = """1.List out all information after "BIOS source of table:". 
If duplicate, list once.

2. mhiffTranslateMccAllowedUhbApTypeCmdVer1 supported by UATS.
List out the value group, which are in 1(LPI), 2(VLP), or 3(AFC)
No need summer table.

3. [prvLarSendLariChangeConfig]: : oemUhbAllowBitMap=<0x" "> convert to binary " "
This binary is very important.
Start from here, all check in test 3. according to this binary.
bit31 Follow Country by Country table for LPI Override
If bit31 set to 1, check bit0 set to 1, skip other bit in DSM Function3
3-1. Print "bit31 = 1, Follow Country by Country table for LPI Override"
If not, print "setting error bit31 (bit0 is not setting to 1)"

If bit31 set to 0, check below value
0 = not allow or disable
1 = allow or enable
3-1. Print bit27 value (0 or 1) VLP Soft AP/Active Scan in UHB in Japan
3-2. Print bit29 value (0 or 1) VLP Follow country by country table for VLP
3-3. Print bit30 value (0 or 1) Follow country by country table for AFC
bit:1 - UHB in USA, 
bit:2 - UHB in Rest of World, 
bit:3 - UHB in EU, 
bit:4 - UHB in Sorth Korea, 
bit:5 - UHB in Brazi, 
bit:6 - UHB in Chile, 
bit:7 - UHB in Japan, 
bit:8 - UHB in Canada, 
bit:9 - UHB in Morocco, 
bit:10 - UHB in Mongolia, 
bit:11 - UHB in Malaysia, 
bit:12 - UHB in Saudi Arabia
3-4. Print "UHB support in (bit)(country)"

4.Check DSM function and Print value
If DSM is not UEFI, DSM use ACPI, skip this.
Print "DSM function setting by ACPI"
If not check below.
Function 0 - WiFi DSM supported functions, this is always required
Function 1 - Disable SRD Active Channels
0 - ETSI 5.8GHz SRD active scan, 
1 - ETSI 5.8GHz SRD passive scan, 
2 - ETSI 5.8GHz SRD disabled.
Function 2 - Supported Indonesia 5.15 - 5.35 GHz band
0 - Set 5.115-5.35GHz to Disable in Indonesia, 
1 - Set 5.115-5.35GHz to Enable (Passive) in Indonesia.
Function 4 - Regulatory Special Configurations Enablements
1 - Enabling DRS for China Location, will work only in the NON CHINA SKU case. In cases where OEM also defines CHINA_SKU in the BIOS WRDD table, the bit will ignored by the driver, 
2 - Enabling new SRRC spec.
Function 5 - M.2 UART Interface Configuration Default as defined in Intel SW Driver/FW, 
1 - Reserved
Function 6 - Control Enablement 11ax on certificated modules Default as defined in Intel Wi-Fi certificated module, 
3 - Enabling Ukraine for 11ax, 
12 - Enabling Russia for 11ax, 
15 - Enabling Ukraine and Russia for 11ax
Function 7 - Control Enablement UNII-4 on certificated modules Default as defined in Intel Wi-Fi certificated module,
3 - Enabling UNII-4 in FCC(US), 
12 - Enabling UNII-4 in ETSI, 
48 - Enabling UNII-4 in ISED(Canada)
Function 8 - Control Indoor usage for enable Soft AP mode
bit:0 - Enabling indoor usage in EU, 
bit:1 - Enabling indoor usage in Japan, 
bit:2 - Enabling indoor usage in China, 
bit:3 - Enabling indoor usage in USA, 
bit:4 - Enabling indoor usage in worldwide
Function 9 - Selective Wi-Fi band operation
bit:0 - Enabling 2.4GHz, 
bit:1 - Enabling 5.2GHz, 
bit:2 - Enabling 5.3GHz, 
bit:3 - Enabling 5.5GHz, 
bit:4 - Enabling 5.8GHz, 
bit:5 - Enabling 5.9GHz, 
bit:6 - Enabling 6.2GHz, 
bit:7 - Enabling 6.5GHz, 
bit:8 - Enabling 6.6GHz, 
bit:9 - Enabling 6.8GHz, 
bit:10 - Enabling 7.0GHz
Function 10 - Energy detection threshold (EDT)
bit:0-3 - EDT revision, 
bit:6 - Enabling EDT for ETSI HB, 
bit:9 - Enabling EDT for FCC UHB, 
bit:13 - Enabling EDT for HB 5G2/3, 
bit:14 - Enabling EDT for HB 5G4, 
bit:15 - Enabling EDT for HB 5G6, 
bit:16 - Enabling EDT for HB 5G8/9, 
bit:17 - Enabling EDT for UHB 6G1, 
bit:18 - Enabling EDT for UHB 6G3, 
bit:19 - Enabling EDT for UHB 6G5, 
bit:20 - Enabling EDT for UHB 6G6, 
bit:21 - Enabling EDT for UHB 6G8, 
bit:22 - Enabling EDT for UHB 7G0
Function 11 - DLVR RFI mitigation Configuration
bit0: DLVR RFI mitigation(0 - enabled, 1 - disabled), 
bit1: DDR RFI mitigation(0 - enabled, 1 - disabled)
Function 12 - Wi-Fi 7 802.11be Support
bit:0 - Force disable all countries
"""
