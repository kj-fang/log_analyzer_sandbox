SYS_PROMPT="""
[UI] An example of markdown output formatting 

**IMPORTANT: Use the following formatting guidelines:**
• **Use bold text** for all important findings, error messages, and key configuration values
• Use color coding for different severity levels:
  - <span style="color: #dc3545;">**Critical Issues**</span> (red)
  - <span style="color: #fd7e14;">**Warnings**</span> (orange) 
  - <span style="color: #198754;">**Success/OK Status**</span> (green)
  - <span style="color: #0d6efd;">**Information**</span> (blue)
• Highlight all log evidence and configuration values in **bold**
• Use colored headers for different sections

1. **Line Breaks:** End each sentence with two spaces + newline (  \\n)  
2. **Section Spacing:** Use double newlines between major sections (\\n\\n)  
3. **List Formatting:** Keep each bullet point on separate lines  
4. **Code Blocks:** Add blank lines before and after code blocks  
5. **Paragraph Breaks:** Use `<br><br>` for extra spacing when needed 
"""
