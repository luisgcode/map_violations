# MAP Violation Email Generator

Professional web application to detect MAP (Minimum Advertised Price) violations and generate personalized emails.

## Features

- Modern web interface with professional Microsoft-style design
- Drag & drop Excel file upload
- Automatic violation detection
- One-click email copy with HTML formatting
- Visual indicators for copied emails
- No data persistence - fresh start every session

## Requirements

- Python 3.8 or higher
- Flask
- pandas
- openpyxl

## Installation

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

## Usage

1. **Start the application:**
```bash
python app_flask.py
```

2. **Open your browser:**
   - Go to `http://localhost:5000`

3. **Upload your Excel file:**
   - Drag & drop or click to browse
   - File must contain columns: `sellers`, `prices`, `U.S. MAP`, `price_difference`, `Description`, `SAP Material`, `seller_links`

4. **Copy emails:**
   - Click "Copy Email" next to each seller
   - Paste directly into Outlook (Ctrl+V)
   - Green checkmark indicates copied emails

## Excel File Requirements

Your Excel file must have these columns:
- `sellers`: Seller/company name
- `prices`: Current advertised price
- `U.S. MAP`: Minimum advertised price
- `price_difference`: Price difference (negative = violation)
- `Description`: Product description
- `SAP Material`: Product SKU
- `seller_links`: URL to product listing (optional)

## Project Structure

```
mav_violations_v1/
├── app_flask.py              # Main Flask application
├── templates/
│   └── index.html           # Web interface
├── requirements.txt          # Python dependencies
├── uploads/                  # Temporary uploaded files (git ignored)
├── output/                   # Generated emails (git ignored)
└── README.md                # This file
```

## Notes

- Application runs locally on your computer
- No data is saved between sessions
- Emails are copied with HTML formatting
- Works with any modern browser
- Files in `uploads/` and `output/` are automatically cleaned on restart

## Created By

Marketing Team - Luis Guaiquirian
Glen Dimplex Americas

## License

Internal company use only.
