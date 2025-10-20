# 📚 My Learning Notes - MAP Project

## ✅ Completed

### Python Basics
**Resource**: Previous experience
**Key insight**: Know basic Python syntax and variables
**Note**: Limited experience overall, learning as we go

### Pandas Library for Excel
**Resource**: https://pandas.pydata.org/docs/
**Key insight**: Pandas reads Excel files and treats them like tables (DataFrames)
**Code example**:
```python
import pandas as pd
df = pd.read_excel('file.xlsx')  # Read Excel
violations = df[df['price_difference'] < 0]  # Filter rows
```
**What I learned**:
- `read_excel()` loads Excel into memory
- Can filter rows with conditions like `df[df['column'] < 0]`
- `groupby()` groups data by a column

### Excel File Structure Analysis
**What we found**:
- 293 rows total
- 26 violations (price_difference < 0)
- 11 unique sellers with violations
- Key columns: sellers, prices, U.S. MAP, price_difference, Description, SAP Material, seller_links

## 🎯 Current Study

### Pandas GroupBy (In Progress)
**Resource**: https://pandas.pydata.org/docs/user_guide/groupby.html
**Goal**: Learn how to group violations by seller name
**My notes**: Will add as we code
**Questions**: How do we get all products for each seller?

### String Formatting in Python
**Resource**: https://docs.python.org/3/tutorial/inputoutput.html
**Goal**: Format prices as currency ($4,199.99)
**My notes**: Will add as we implement templates

### File I/O in Python
**Resource**: https://docs.python.org/3/tutorial/inputoutput.html#reading-and-writing-files
**Goal**: Write formatted emails to .txt files
**My notes**: Will add when creating output files

## 📝 Concepts to Learn Later

### Pathlib for File Management
**Why**: Clean file/folder operations
**When**: Phase 3 (creating output files)

### Error Handling (try/except)
**Why**: Handle missing files gracefully
**When**: Phase 4 (main script)

### Command Line Arguments
**Why**: Let user specify Excel file
**When**: Phase 4 (if needed)

## 💡 Key Takeaways So Far:
- Excel has 15 columns but we only need 7 for emails
- Violation = when price_difference is negative
- Need to group multiple violations per seller into one email
- Output must maintain formatting for Outlook