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
    """Generate email for single product violation with HTML formatting"""
    sku = product_row['SAP Material']
    description = product_row['Description']
    map_price = product_row['U.S. MAP']
    current_price = product_row['prices']
    product_link = product_row.get('seller_links', 'N/A')

    subject = "IMMEDIATE ACTION REQUIRED - Glen Dimplex MAP Violation (1 Product)"

    # Build product line with clickable link
    # Style prices to be larger and bold to stand out
    map_html = f"<span style='font-size:15px; font-weight:700;'>${map_price:.2f}</span>"
    your_price_html = f"<span style='font-size:16px; font-weight:800; color:#e53e3e;'>${current_price:.2f}</span>"

    product_info = (
        f"<p><strong>SKU {sku}</strong> ({description})<br>"
        f"<strong>MAP:</strong> {map_html} &nbsp;|&nbsp; <strong>Your Price:</strong> {your_price_html}</p>"
    )

    if product_link and product_link != 'N/A' and str(product_link).strip() and product_link != 'nan':
        product_info += f"<p><strong>Product Link:</strong> <a href='{product_link}'>{product_link}</a></p>"

    body = f"""<div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
<p>Hello,</p>

<p>Your company is in violation of <strong>Glen Dimplex Americas Minimum Advertised Price (MAP) Policy</strong>.</p>

{product_info}

<p>Per our MAP policy, you are required to update the pricing in line with our MAP policy <strong style='color: #c53030;'>within 24 hours</strong>. If this violation is not corrected, GDA reserves the right to refuse purchase orders, stop future shipments, and/or suspend accounts is at our discretion which may or may not be permanent.</p>

<p>Please note that we have had a price change effective from <strong>October 1st, 2025</strong>, and the updated price lists have been provided to your distributors.</p>

<p>If you have any questions about this MAP violation, please respond directly to this email. If you are not the correct person to receive this notice, please reply with the name, title, and contact information of the correct individual.</p>

<p>Sincerely,<br>
<strong>Glen Dimplex Americas MAP Enforcement Team</strong></p>
</div>"""

    return {"subject": subject, "body": body}

def generate_email_multiple_products(products_df):
    """Generate email for multiple product violations with HTML formatting"""
    num_products = len(products_df)

    subject = f"IMMEDIATE ACTION REQUIRED - Glen Dimplex MAP Violations ({num_products} Products)"

    product_list = []
    for idx, row in products_df.iterrows():
        sku = row['SAP Material']
        description = row['Description']
        map_price = row['U.S. MAP']
        current_price = row['prices']
        product_link = row.get('seller_links', 'N/A')

        # Build product line with clickable link
        # Style prices to be larger and bold
        map_html = f"<span style='font-size:15px; font-weight:700;'>${map_price:.2f}</span>"
        your_price_html = f"<span style='font-size:16px; font-weight:800; color:#e53e3e;'>${current_price:.2f}</span>"

        product_line = (
            f"<li><strong>SKU {sku}</strong> ({description})<br>"
            f"<strong>MAP:</strong> {map_html} &nbsp;|&nbsp; <strong>Your Price:</strong> {your_price_html}"
        )
        if product_link and product_link != 'N/A' and str(product_link).strip() and product_link != 'nan':
            product_line += f"<br><strong>Link:</strong> <a href='{product_link}'>{product_link}</a>"
        product_line += "</li>"

        product_list.append(product_line)

    products_html = "\n".join(product_list)

    body = f"""<div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
<p>Hello,</p>

<p>Your company is in violation of <strong>Glen Dimplex Americas Minimum Advertised Price (MAP) Policy</strong>. The following Dimplex SKUs are currently being sold below MAP:</p>

<ul style="margin: 20px 0; padding-left: 20px;">
{products_html}
</ul>

<p>Per our MAP policy, you are required to update the pricing in line with our MAP policy <strong style='color: #c53030;'>within 24 hours</strong>. If this violation is not corrected, GDA reserves the right to refuse purchase orders, stop future shipments, and/or suspend accounts is at our discretion which may or may not be permanent.</p>

<p>Please note that we have had a price change effective from <strong>October 1st, 2025</strong>, and the updated price lists have been provided to your distributors.</p>

<p>If you have any questions about this MAP violation, please respond directly to this email. If you are not the correct person to receive this notice, please reply with the name, title, and contact information of the correct individual.</p>

<p>Sincerely,<br>
<strong>Glen Dimplex Americas MAP Enforcement Team</strong></p>
</div>"""

    return {"subject": subject, "body": body}

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
            email_data = generate_email_single_product(violations_df.iloc[0])
        else:
            email_data = generate_email_multiple_products(violations_df)

        filename = f"email_{clean_filename(seller_name)}.html"
        # Combine subject and body for file storage
        email_content = f"Subject: {email_data['subject']}\n\n{email_data['body']}"
        emails[filename] = {"content": email_content, "subject": email_data['subject'], "body": email_data['body']}

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

        # Save emails to files (use .txt extension for download/consistency)
        for filename, email_data in emails.items():
            # if generated filename ends with .html, also save a .txt version for downloads
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(email_data['content'])

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
            'sellers': sellers_data,
            'uploaded_filename': file.filename
        })

    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/get-email-content/<filename>')
def get_email_content(filename):
    """Get email content as JSON for clipboard copy with HTML format"""
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            full_content = f.read()

        # Split subject and body
        if 'Subject:' in full_content:
            parts = full_content.split('\n\n', 1)
            subject = parts[0].replace('Subject: ', '')
            body = parts[1] if len(parts) > 1 else ''
        else:
            subject = ''
            body = full_content

        return jsonify({
            'subject': subject,
            'body': body
        })
    except Exception as e:
        return jsonify({'error': f'File not found: {str(e)}'}), 404

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
    app.run(debug=True, host='127.0.0.1', port=5000)
