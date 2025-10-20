from flask import Flask, render_template, request, send_file, jsonify
import pandas as pd
from pathlib import Path
from datetime import datetime
import re
import io
import zipfile
import os

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
Path(OUTPUT_FOLDER).mkdir(exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def read_violations(file_path):
    """Read Excel and filter violations"""
    df = pd.read_excel(file_path)
    violations = df[df['price_difference'] < 0].copy()
    return violations, len(df)

def group_by_seller(violations_df):
    """Group violations by seller"""
    grouped = {}
    for seller in violations_df['sellers'].unique():
        seller_violations = violations_df[violations_df['sellers'] == seller]
        grouped[seller] = seller_violations
    return grouped

def generate_email_single_product(product_row):
    """Generate email for single product violation"""
    sku = product_row['SAP Material']
    description = product_row['Description']
    map_price = product_row['U.S. MAP']
    current_price = product_row['prices']
    product_link = product_row.get('seller_links', 'N/A')

    subject = "Subject: IMMEDIATE ACTION REQUIRED - Glen Dimplex MAP Violation (1 Product)"

    # Build product line with link
    product_line = f"SKU {sku} ({description}): MAP ${map_price:.2f}, Your Price: ${current_price:.2f}"
    if product_link and product_link != 'N/A' and str(product_link).strip():
        product_line += f"\nProduct Link: {product_link}"

    body = f"""Hello,
Your company is in violation of Glen Dimplex Americas Minimum Advertised Price (MAP) Policy.

{product_line}

Per our MAP policy, you are required to update the pricing in line with our MAP policy within 24 hours. If this violation is not corrected, GDA reserves the right to refuse purchase orders, stop future shipments, and/or suspend accounts is at our discretion which may or may not be permanent.

Please note that we have had a price change effective from October 1st, 2025, and the updated price lists have been provided to your distributors.

If you have any questions about this MAP violation, please respond directly to this email. If you are not the correct person to receive this notice, please reply with the name, title, and contact information of the correct individual.

Sincerely,
Glen Dimplex Americas MAP Enforcement Team"""

    return f"{subject}\n\n{body}"

def generate_email_multiple_products(products_df):
    """Generate email for multiple product violations"""
    num_products = len(products_df)

    subject = f"Subject: IMMEDIATE ACTION REQUIRED - Glen Dimplex MAP Violations ({num_products} Products)"

    product_list = []
    for idx, row in products_df.iterrows():
        sku = row['SAP Material']
        description = row['Description']
        map_price = row['U.S. MAP']
        current_price = row['prices']
        product_link = row.get('seller_links', 'N/A')

        # Build product line with link
        product_line = f"- SKU {sku} ({description}): MAP ${map_price:.2f}, Your Price: ${current_price:.2f}"
        if product_link and product_link != 'N/A' and str(product_link).strip():
            product_line += f"\n  Link: {product_link}"

        product_list.append(product_line)

    products_text = "\n".join(product_list)

    body = f"""Hello,
Your company is in violation of Glen Dimplex Americas Minimum Advertised Price (MAP) Policy. The following Dimplex SKUs are currently being sold below MAP:

{products_text}

Per our MAP policy, you are required to update the pricing in line with our MAP policy within 24 hours. If this violation is not corrected, GDA reserves the right to refuse purchase orders, stop future shipments, and/or suspend accounts is at our discretion which may or may not be permanent.

Please note that we have had a price change effective from October 1st, 2025, and the updated price lists have been provided to your distributors.

If you have any questions about this MAP violation, please respond directly to this email. If you are not the correct person to receive this notice, please reply with the name, title, and contact information of the correct individual.

Sincerely,
Glen Dimplex Americas MAP Enforcement Team"""

    return f"{subject}\n\n{body}"

def clean_filename(seller_name):
    """Clean seller name for filename"""
    cleaned = seller_name.replace(' ', '_')
    cleaned = re.sub(r'[^\w\-_]', '', cleaned)
    return cleaned

def generate_emails(grouped_violations):
    """Generate all email files"""
    emails = {}
    for seller_name, violations_df in grouped_violations.items():
        num_violations = len(violations_df)

        if num_violations == 1:
            email_content = generate_email_single_product(violations_df.iloc[0])
        else:
            email_content = generate_email_multiple_products(violations_df)

        filename = f"email_{clean_filename(seller_name)}.txt"
        emails[filename] = email_content

    return emails

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and process violations"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'Please upload an Excel file (.xlsx or .xls)'}), 400

    try:
        # Save uploaded file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        # Process violations
        violations_df, total_rows = read_violations(filepath)

        if len(violations_df) == 0:
            return jsonify({
                'success': True,
                'no_violations': True,
                'total_rows': total_rows,
                'message': 'No violations found! All sellers are complying with MAP policy.'
            })

        # Group by seller
        grouped_violations = group_by_seller(violations_df)

        # Generate emails
        emails = generate_emails(grouped_violations)

        # Save emails to files
        for filename, content in emails.items():
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)

        # Prepare response data
        sellers_data = []
        for seller_name, seller_violations in grouped_violations.items():
            sellers_data.append({
                'name': seller_name,
                'violations': len(seller_violations),
                'filename': f"email_{clean_filename(seller_name)}.txt"
            })

        return jsonify({
            'success': True,
            'no_violations': False,
            'total_rows': total_rows,
            'total_violations': len(violations_df),
            'num_sellers': len(grouped_violations),
            'sellers': sellers_data
        })

    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download individual email file"""
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        return send_file(file_path, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'error': f'File not found: {str(e)}'}), 404

@app.route('/download-all')
def download_all():
    """Download all emails as ZIP"""
    try:
        # Create ZIP file in memory
        memory_file = io.BytesIO()

        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            output_path = Path(app.config['OUTPUT_FOLDER'])
            for file_path in output_path.glob('*.txt'):
                zf.write(file_path, file_path.name)

        memory_file.seek(0)

        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'map_violation_emails_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
        )

    except Exception as e:
        return jsonify({'error': f'Error creating ZIP: {str(e)}'}), 500

if __name__ == '__main__':
    print("=" * 80)
    print("MAP VIOLATION EMAIL GENERATOR")
    print("=" * 80)
    print("\nStarting web server...")
    print("Open your browser and go to: http://localhost:5000")
    print("\nPress CTRL+C to stop the server")
    print("=" * 80)
    app.run(debug=True, host='0.0.0.0', port=5000)
