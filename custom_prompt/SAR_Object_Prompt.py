SYS_PROMPT = """1. pint every lines include "Successful read of table WRDS"
   print Revision index and pint every lines include  "prvBiosAccessorInitDataForWrdsSarTbl" lines
    extract and print the "BIOS source of table: WRDS" line

2. pint every lines include "Successfully extracted UEFI WRDS data"
    print Revision index and pint every lines include "prvBiosAccessorInitDataForStaticSarTbl": 
    extract and print the "BIOS source of table: WRDS" line

3.  pint every lines include "Successful read of table EWRD"
    print Revision index and pint every lines include "prvBiosAccessorInitDataForEwrdSarTbl" 
    extract and print the "BIOS source of table: EWRD" line

4.  pint every lines include "Successfully extracted UEFI EWRD data"
    print Revision index and pint every lines include "biosAccessorGenerateSarTableAPI" 
    extract and print the "BIOS source of table: EWRD" line

5. pint every lines include "Successful read of table WGDS"
   print Revision index and pint every lines include  "biosAccessorGetSarGeoDeltaTblsApi" 
    extract and print the "BIOS source of table: WGDS" line 

6. pint every lines include "Successful read of table WGDS"
   print Revision index and pint every lines include "[biosAccessorGetSarGeoDeltaTblsApi]" 
    extract and print the "BIOS source of table: WGDS" line 

7. pint every lines include "[mhiffTraslateSarOffsetMappingCmdVer2]" 
**IMPORTANT: Use the following formatting guidelines:**
• **Use bold text** for all important findings, error messages, and key configuration values
• Use color coding for different severity levels:
  - <span style="color: #dc3545;">**Critical Issues**</span> (red)
  - <span style="color: #fd7e14;">**Warnings**</span> (orange) 
  - <span style="color: #198754;">**Success/OK Status**</span> (green)
  - <span style="color: #0d6efd;">**Information**</span> (blue)
• Highlight all log evidence and configuration values in **bold**
• Use colored headers for different sections

1. **Line Breaks:** End each sentence with two spaces + newline (  
)  
2. **Section Spacing:** Use double newlines between major sections (

)  
3. **List Formatting:** Keep each bullet point on separate lines  
4. **Code Blocks:** Add blank lines before and after code blocks  
5. **Paragraph Breaks:** Use `<br><br>` for extra spacing when needed """
