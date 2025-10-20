# 🗺️ MAP Violation Email Generator - Project Roadmap

## 🎯 Mission:
Automate the detection of MAP (Minimum Advertised Price) violations from daily Excel reports and generate personalized enforcement emails, eliminating manual review and reducing email preparation time from hours to minutes.

## 📅 Timeline & Phases:

### ✅ Phase 0: Setup & Analysis (Completed)
- [x] Install Python 3.14 and required libraries (pandas, openpyxl)
- [x] Analyze Excel file structure and understand data
- [x] Identify violation logic (price_difference < 0)
- [x] Create .gitignore to protect company data
- [x] Create professional README.md for GitHub

### 🔄 Phase 1: Data Processing (In Progress)
- [ ] Read Excel file with pandas
- [ ] Filter violations (price_difference < 0)
- [ ] Group violations by seller
- [ ] Generate summary report

### 📝 Phase 2: Email Template Generation
- [ ] Create singular email template (1 product)
- [ ] Create plural email template (multiple products)
- [ ] Include all required data: SKU, Description, Prices, Links
- [ ] Format subject line with product count

### 📝 Phase 3: File Output System
- [ ] Create output/ folder structure
- [ ] Generate individual .txt files per seller
- [ ] Format: Subject line + blank + Body
- [ ] Clean seller names for filenames
- [ ] Preserve formatting for Outlook compatibility

### 📝 Phase 4: Main Script & User Experience
- [ ] Create simple `generate_emails.py` script
- [ ] Auto-detect Excel file or allow user input
- [ ] Show processing summary
- [ ] Confirm successful generation
- [ ] Handle errors gracefully

### 📝 Phase 5: Testing & Production
- [ ] Test with sample file (26 violations, 11 sellers)
- [ ] Verify all 11 email files generated correctly
- [ ] Copy/paste test in Outlook (formatting check)
- [ ] Final adjustments
- [ ] Documentation for daily use

## 🎯 Success Metrics:
- [x] System correctly identifies all violations (price_difference < 0)
- [ ] Generates correct number of email files (1 per seller)
- [ ] Email format is perfect for Outlook copy/paste
- [ ] Process takes < 30 seconds from Excel to emails
- [ ] Non-technical user can run with single command
- [ ] Zero manual data entry required

## 📚 Key Resources:
1. Pandas Documentation - https://pandas.pydata.org/docs/
2. Python pathlib - https://docs.python.org/3/library/pathlib.html
3. String formatting - https://docs.python.org/3/library/string.html

## 📈 Progress Tracking:
- [x] Phase 0: Setup & Analysis ✅
- [ ] Phase 1: Data Processing (IN PROGRESS)
- [ ] Phase 2: Email Templates
- [ ] Phase 3: File Output
- [ ] Phase 4: Main Script
- [ ] Phase 5: Testing & Production

## 💡 Business Impact:
**Before**: 1-2 hours daily reviewing Excel + manually writing emails
**After**: < 5 minutes to generate all emails, just copy/paste to Outlook
**Time Saved**: ~8-10 hours per week