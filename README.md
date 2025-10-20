# MAP Violation Email Generator

Automated system to detect MAP (Minimum Advertised Price) violations and generate personalized emails ready to send.

## Description

This project reads Excel files with price data, identifies sellers who are violating minimum advertised price policies, and generates individual emails ready to copy and paste into Outlook.

## Features

- ✅ Automatic reading of Excel files with price data
- ✅ Violation detection based on price difference
- ✅ Grouping of multiple violations by seller
- ✅ Generation of personalized emails (singular/plural)
- ✅ Format ready to copy/paste into Outlook
- ✅ Individual output files per seller

## Requirements

- Python 3.x
- pandas
- openpyxl

## Installation

```bash
pip install pandas openpyxl
```

## Usage

1. Place your Excel file in the project folder
2. Make sure you have the email template (`MAP-mail-template`)
3. Run the main script:

```bash
python generate_emails.py
```

4. Generated emails will be in the `output/` folder
5. Copy and paste each email into Outlook

## Project Structure

```
map-dimplex/
├── generate_emails.py          # Main script
├── MAP-mail-template           # Email template
├── output/                     # Generated emails (ignored by git)
├── .gitignore                  # Files to ignore
└── README.md                   # This file
```

## Notes

- Excel files and the output/ folder are excluded from the repository as they contain confidential information
- The system does NOT connect to Outlook automatically (due to corporate restrictions)
- User must manually copy and paste each email

## Configuration

To use this project:

1. Add your Excel file with the following minimum columns:
   - `sellers`: Seller name
   - `prices`: Current price
   - `U.S. MAP`: Minimum allowed price
   - `price_difference`: Difference (negative = violation)
   - `Description`: Product description
   - `SAP Material`: SKU code
   - `seller_links`: Links to products

2. Customize the `MAP-mail-template` template according to your needs

## License

Internal company use.
