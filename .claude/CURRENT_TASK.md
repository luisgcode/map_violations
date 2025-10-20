# 📚 Current Task - MAP Email Generator Project

## 🎯 PROJECT STATUS: Phase 1 - In Progress

### What We're Building:
Python system that reads Excel files with pricing data, detects MAP (Minimum Advertised Price) violations, and generates personalized emails ready to copy/paste into Outlook.

### Current Phase: Fase 1 - Reading Excel & Filtering Violations
**Status**: About to start
**Goal**: Create script that reads Excel, filters violations (price_difference < 0), groups by seller

## 📋 TODO LIST:

### ✅ Completed:
- [x] Python & libraries installed (pandas, openpyxl)
- [x] Analyzed sample Excel file structure
- [x] Created .gitignore to protect company data
- [x] Created README.md for GitHub
- [x] Identified 26 violations from 11 sellers in sample file

### 🔄 In Progress:
- [ ] **Fase 1**: Create script to read Excel and filter violations
  - Read Excel file with pandas
  - Filter rows where price_difference < 0
  - Group violations by seller
  - Show summary report

### 📝 Pending:
- [ ] **Fase 2**: Generate email templates (singular/plural)
- [ ] **Fase 3**: Create individual output files per seller
- [ ] **Fase 4**: Create main user-friendly script
- [ ] **Fase 5**: Testing and validation with Outlook

## 📊 Excel File Structure:
- **UPC**: Product code
- **sellers**: Seller/client name
- **prices**: Current selling price
- **U.S. MAP**: Minimum advertised price allowed
- **price_difference**: Difference (negative = violation)
- **Description**: Product description
- **SAP Material**: SKU code
- **seller_links**: Amazon product links

## 📧 Email Requirements:
- One email per seller (group all violations)
- Include: SKU, Description, MAP price, Current price, Link
- Subject format: "IMMEDIATE ACTION REQUIRED - Glen Dimplex MAP Violations (X Products)"
- Template: `MAP-mail-template` (adapted for singular/plural)
- Output: Individual .txt files per seller, ready for Outlook copy/paste

## 🔄 To continue with Claude:
"Read my CURRENT_TASK.md in .claude folder to see where we are in the MAP project"