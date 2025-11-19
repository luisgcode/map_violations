from flask import Flask, render_template, request, send_file, jsonify
import pandas as pd
from pathlib import Path
from datetime import datetime, date
import re
import io
import zipfile
import os
import sqlite3
from contextlib import contextmanager

app = Flask(__name__)

# Database configuration
DB_PATH = 'violations_tracker.db'

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
Path(OUTPUT_FOLDER).mkdir(exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size


# ============================================================================
# DATABASE FUNCTIONS - VIOLATION TRACKER
# ============================================================================

@contextmanager
def get_db():
    """Database connection context manager"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_database():
    """Initialize database tables if they don't exist"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Violations tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_name TEXT NOT NULL,
                sku TEXT NOT NULL,
                product_description TEXT,
                current_price REAL,
                map_price REAL,
                first_detected_date TEXT NOT NULL,
                last_seen_date TEXT NOT NULL,
                days_active INTEGER DEFAULT 0,
                status TEXT DEFAULT 'ACTIVE',
                seller_link TEXT,
                pending_approval INTEGER DEFAULT 0,
                first_email_sent_date TEXT DEFAULT NULL,
                second_email_sent_date TEXT DEFAULT NULL,
                dns_added_date TEXT DEFAULT NULL,
                UNIQUE(seller_name, sku)
            )
        ''')

        # Upload history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS upload_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                upload_date TEXT NOT NULL UNIQUE,
                upload_time TEXT NOT NULL,
                filename TEXT,
                violations_count INTEGER
            )
        ''')

def check_upload_today():
    """Check if file was already uploaded today"""
    today = date.today().isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        result = cursor.execute(
            'SELECT * FROM upload_log WHERE upload_date = ?',
            (today,)
        ).fetchone()
        return dict(result) if result else None

def log_upload(filename, violations_count):
    """Log today's upload"""
    today = date.today().isoformat()
    now = datetime.now().strftime('%H:%M:%S')

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO upload_log
            (upload_date, upload_time, filename, violations_count)
            VALUES (?, ?, ?, ?)
        ''', (today, now, filename, violations_count))

def update_violations_tracker(violations_df):
    """Update tracker with new violations data
    
    GENERAL RULE: Multiple sellers can have the same SKU - each combination (seller, sku) 
    is handled independently. Only violations that do NOT appear in current Excel are marked 
    as RESOLVED. Ensures complete synchronization with daily Excel.
    """
    today = date.today().isoformat()

    with get_db() as conn:
        cursor = conn.cursor()

        # PASO 1: Procesar todas las violaciones actuales del Excel
        current_violations = set()
        new_violations = 0
        updated_violations = 0

        for _, row in violations_df.iterrows():
            seller = row['sellers']
            sku = row['SAP Material']
            key = (seller, sku)
            current_violations.add(key)

            # Check if violation exists in tracker
            existing = cursor.execute(
                'SELECT * FROM violations WHERE seller_name = ? AND sku = ?',
                (seller, sku)
            ).fetchone()

            if existing:
                # Update existing violation - ALWAYS reactivate to ACTIVE if in Excel
                first_date = existing['first_detected_date']
                days = (date.today() - date.fromisoformat(first_date)).days

                cursor.execute('''
                    UPDATE violations
                    SET last_seen_date = ?,
                        days_active = ?,
                        current_price = ?,
                        map_price = ?,
                        product_description = ?,
                        seller_link = ?,
                        status = 'ACTIVE'
                    WHERE seller_name = ? AND sku = ?
                ''', (
                    today, days,
                    float(row['prices']), float(row['U.S. MAP']),
                    row['Description'], row.get('seller_links', ''),
                    seller, sku
                ))
                updated_violations += 1
            else:
                # Insert new violation
                cursor.execute('''
                    INSERT INTO violations
                    (seller_name, sku, product_description, current_price, map_price,
                     first_detected_date, last_seen_date, days_active, status,
                     seller_link, pending_approval)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 0, 'ACTIVE', ?, 0)
                ''', (
                    seller, sku, row['Description'],
                    float(row['prices']), float(row['U.S. MAP']),
                    today, today, row.get('seller_links', '')
                ))
                new_violations += 1

        # STEP 2: Mark as RESOLVED only violations that are NOT in current Excel
        cursor.execute(
            'SELECT seller_name, sku FROM violations WHERE status = "ACTIVE"'
        )
        tracked_violations = cursor.fetchall()

        resolved_violations = 0
        for violation in tracked_violations:
            key = (violation['seller_name'], violation['sku'])
            if key not in current_violations:
                cursor.execute('''
                    UPDATE violations
                    SET status = 'RESOLVED'
                    WHERE seller_name = ? AND sku = ?
                ''', key)
                resolved_violations += 1
        
        # Sync log for debugging
        print(f"Synchronization completed:")
        print(f"  - New violations: {new_violations}")
        print(f"  - Updated violations: {updated_violations}")  
        print(f"  - Resolved violations: {resolved_violations}")
        print(f"  - Total violations in Excel: {len(current_violations)}")

def get_active_violations_grouped():
    """Get active violations grouped by seller"""
    with get_db() as conn:
        cursor = conn.cursor()
        violations = cursor.execute('''
            SELECT * FROM violations
            WHERE status = 'ACTIVE'
            ORDER BY seller_name, days_active DESC, sku
        ''').fetchall()

        # Group by seller
        grouped = {}
        for v in violations:
            seller = v['seller_name']
            if seller not in grouped:
                grouped[seller] = []
            grouped[seller].append(dict(v))

        return grouped

# Initialize database on startup
init_database()

# ============================================================================
# EXCLUDED SELLERS CONFIGURATION
# ============================================================================
# Add seller names here that you don't want to process for emails
# These sellers will be filtered out from the main grid but shown in statistics
# 
# TO ADD NEW EXCLUDED SELLERS:
# 1. Add the seller name to the list below (case variations supported)
# 2. Save this file
# 3. Restart the application
#
def load_excluded_sellers():
    """Load excluded sellers from configuration file"""
    excluded_sellers = []
    config_file = 'excluded_sellers.txt'
    
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip().lower()  # Normalize to lowercase immediately
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        excluded_sellers.append(line)
        else:
            # Default excluded sellers if config file doesn't exist (all lowercase)
            excluded_sellers = [
                'amazon.com',
                'lsg fireplaces',
            ]
    except Exception as e:
        print(f"Error reading excluded sellers config: {e}")
        # Fallback to default list (all lowercase)
        excluded_sellers = ['amazon.com', 'lsg fireplaces']
    
    return excluded_sellers

def get_excluded_sellers_lower():
    """Get current list of excluded sellers (already normalized to lowercase)"""
    return load_excluded_sellers()  # Already lowercase from load function

# ============================================================================
# SELLER CONTACTS CONFIGURATION
# ============================================================================
def load_seller_contacts():
    """Load seller contacts from configuration file"""
    contacts = {}
    config_file = 'seller_contacts.txt'

    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        parts = line.split('|')
                        if len(parts) >= 4:
                            seller_name = parts[0].strip()
                            email = parts[1].strip()
                            phone = parts[2].strip()
                            website = parts[3].strip()

                            contacts[seller_name.lower()] = {
                                'email': email if email != 'N/A' else None,
                                'phone': phone if phone != 'N/A' else None,
                                'website': website if website != 'N/A' else None
                            }
    except Exception as e:
        print(f"Error reading seller contacts config: {e}")

    return contacts

def get_seller_contact(seller_name):
    """Get contact information for a specific seller"""
    contacts = load_seller_contacts()
    return contacts.get(seller_name.lower().strip(), {
        'email': None,
        'phone': None,
        'website': None
    })

def validate_excel_columns(df):
    """Validate that all required columns are present"""
    required_columns = ['sellers', 'prices', 'U.S. MAP', 'price_difference', 'Description', 'SAP Material', 'seller_links']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
    
    return True

def read_violations(file_path):
    """Read Excel and filter violations with validation"""
    try:
        df = pd.read_excel(file_path)
        
        # Validate columns exist
        validate_excel_columns(df)
        
        # Check for empty dataframe
        if df.empty:
            raise ValueError("Excel file is empty")
        
        # Validate data types and values
        if not pd.api.types.is_numeric_dtype(df['prices']):
            raise ValueError("'prices' column must contain numeric values")
        
        if not pd.api.types.is_numeric_dtype(df['U.S. MAP']):
            raise ValueError("'U.S. MAP' column must contain numeric values")
            
        if not pd.api.types.is_numeric_dtype(df['price_difference']):
            raise ValueError("'price_difference' column must contain numeric values")
        
        # Filter violations (price_difference < 0 means current price < MAP price)
        violations = df[df['price_difference'] < 0].copy()
        
        # Validate that we have actual violations
        if len(violations) == 0:
            return violations, len(df)  # No violations found, but data is valid
        
        # Additional validation for violations
        for idx, row in violations.iterrows():
            if pd.isna(row['sellers']) or str(row['sellers']).strip() == '':
                raise ValueError(f"Row {idx + 1}: Seller name is empty")
            
            if pd.isna(row['Description']) or str(row['Description']).strip() == '':
                raise ValueError(f"Row {idx + 1}: Description is empty")
            
            if pd.isna(row['SAP Material']) or str(row['SAP Material']).strip() == '':
                raise ValueError(f"Row {idx + 1}: SAP Material is empty")
        
        return violations, len(df)
        
    except Exception as e:
        print(f"Error reading Excel file: {str(e)}")
        raise

# ============================================================================
# UTILITY FUNCTIONS FOR CODE OPTIMIZATION
# ============================================================================

def filter_excluded_sellers_from_grouped(grouped_data):
    """
    Utility function to filter out excluded sellers from grouped violation data.
    Reduces code duplication in multiple places where this filtering is needed.
    
    Args:
        grouped_data (dict): Dictionary with seller names as keys and violation lists as values
    
    Returns:
        tuple: (filtered_grouped_data, excluded_count)
    """
    excluded_sellers_lower = get_excluded_sellers_lower()
    filtered_grouped = {}
    excluded_count = 0
    
    for seller_name, violations_list in grouped_data.items():
        seller_normalized = seller_name.lower().strip()
        if seller_normalized in excluded_sellers_lower:
            excluded_count += len(violations_list)
        else:
            filtered_grouped[seller_name] = violations_list
    
    return filtered_grouped, excluded_count

def create_error_response(message, status_code=500):
    """
    Utility function to create standardized error responses.
    Reduces code duplication in error handling.
    
    Args:
        message (str): Error message
        status_code (int): HTTP status code (default 500)
    
    Returns:
        tuple: (jsonify response, status_code)
    """
    return jsonify({'error': message}), status_code

def create_success_response(data=None):
    """
    Utility function to create standardized success responses.
    
    Args:
        data (dict): Additional data to include in response
    
    Returns:
        flask.Response: JSON response with success=True
    """
    response_data = {'success': True}
    if data:
        response_data.update(data)
    return jsonify(response_data)

def separate_sellers(violations_df):
    """Separate violations into included and excluded sellers"""
    if violations_df.empty:
        return pd.DataFrame(), pd.DataFrame()
    
    excluded_sellers_lower = get_excluded_sellers_lower()
    
    # Debug: Print all unique sellers and exclusion list
    unique_sellers = violations_df['sellers'].str.lower().str.strip().unique()
    
    # Apply exclusion filter
    included_mask = ~violations_df['sellers'].str.lower().str.strip().isin(excluded_sellers_lower)
    excluded_mask = violations_df['sellers'].str.lower().str.strip().isin(excluded_sellers_lower)
    
    included_violations = violations_df[included_mask].copy()
    excluded_violations = violations_df[excluded_mask].copy()
    
    return included_violations, excluded_violations

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
    """Handle file upload and process violations with tracking"""
    if 'file' not in request.files:
        return create_error_response('No file uploaded', 400)

    file = request.files['file']

    if file.filename == '':
        return create_error_response('No file selected', 400)

    if not file.filename.endswith(('.xlsx', '.xls')):
        return create_error_response('Please upload an Excel file (.xlsx or .xls)', 400)

    try:
        # Check if already uploaded today
        existing_upload = check_upload_today()
        force_upload = request.form.get('force_upload') == 'true'

        if existing_upload and not force_upload:
            # Return existing tracker data with complete structure
            grouped = get_active_violations_grouped()
            
            # APPLY EXCLUSIONS TO EXISTING TRACKER DATA
            grouped, excluded_count = filter_excluded_sellers_from_grouped(grouped)
            
            # Prepare complete response data like in normal flow
            sellers_data = []
            total_day1 = 0
            total_day2 = 0
            total_day3 = 0
            total_active = 0
            unique_violators = len(grouped)  # Number of unique violators

            with get_db() as conn:
                cursor = conn.cursor()
                
                for seller_name, violations_list in grouped.items():
                    contact_info = get_seller_contact(seller_name)

                    # Process each product violation
                    products = []
                    for v in violations_list:
                        total_active += 1
                        # Determine day status
                        if v['days_active'] == 0:
                            day_status = 'DAY_1'
                            total_day1 += 1
                        elif v['days_active'] == 1:
                            day_status = 'DAY_2'
                            total_day2 += 1
                        else:  # days_active >= 2
                            day_status = 'DAY_3'
                            total_day3 += 1

                        products.append({
                            'id': v['id'],
                            'sku': v['sku'],
                            'description': v['product_description'],
                            'current_price': v['current_price'],
                            'map_price': v['map_price'],
                            'first_detected': v['first_detected_date'],
                            'days_active': v['days_active'],
                            'day_status': day_status,
                            'first_email_sent': bool(v['first_email_sent_date']),
                            'second_email_sent': bool(v['second_email_sent_date']),
                            'pending_approval': bool(v.get('pending_approval', 0)),
                            'in_dns': bool(v.get('dns_added_date')),
                            'seller_link': v['seller_link'],
                            'first_email_sent_date': v['first_email_sent_date'],
                            'second_email_sent_date': v['second_email_sent_date'],
                            'dns_added_date': v['dns_added_date']
                        })

                    # Check if ANY product in this seller has pending_approval
                    has_pending = any(p['pending_approval'] for p in products)
                    has_in_dns = any(p['in_dns'] for p in products)
                    
                    # Get email tracking status for this seller
                    cursor.execute("""
                        SELECT 
                            COUNT(CASE WHEN first_email_sent_date IS NOT NULL THEN 1 END) as first_emails_sent,
                            COUNT(CASE WHEN second_email_sent_date IS NOT NULL THEN 1 END) as second_emails_sent,
                            MAX(first_email_sent_date) as first_email_date,
                            MAX(second_email_sent_date) as second_email_date,
                            MAX(dns_added_date) as dns_added_date
                        FROM violations 
                        WHERE seller_name = ? AND status = 'ACTIVE'
                    """, (seller_name,))
                    
                    tracking_data = cursor.fetchone()

                    sellers_data.append({
                        'name': seller_name,
                        'contact': contact_info,
                        'products': products,
                        'pending_approval': has_pending,
                        'in_dns': has_in_dns,
                        'first_emails_sent': tracking_data[0] or 0,
                        'second_emails_sent': tracking_data[1] or 0,
                        'first_email_date': tracking_data[2],
                        'second_email_date': tracking_data[3],
                        'dns_added_date': tracking_data[4]
                    })

            return jsonify({
                'success': True,
                'duplicate_detected': True,
                'tracking_enabled': True,
                'existing_upload': existing_upload,
                'total_active_violations': total_active,
                'unique_violators': unique_violators,
                'day_1_count': total_day1,
                'day_2_count': total_day2,
                'day_3_count': total_day3,
                'sellers': sellers_data,
                'uploaded_filename': file.filename,
                'upload_date': existing_upload['upload_date'],
                'message': f"File already uploaded today at {existing_upload['upload_time']}. Showing current tracker data."
            })

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
                'uploaded_filename': file.filename,
                'upload_date': date.today().isoformat(),
                'message': 'No violations found! All sellers are complying with MAP policy.'
            })

        # Separate included and excluded sellers
        included_violations, _ = separate_sellers(violations_df)

        # Check if we have any processable violations after excluding sellers
        if len(included_violations) == 0:
            return jsonify({
                'success': True,
                'no_violations': True,
                'total_rows': total_rows,
                'message': 'All violations are from excluded sellers.'
            })

        # UPDATE TRACKER with violations
        update_violations_tracker(included_violations)

        # LOG UPLOAD
        log_upload(file.filename, len(included_violations))

        # GET TRACKED VIOLATIONS (grouped by seller)
        grouped_tracked = get_active_violations_grouped()

        # Prepare response data with tracking info
        sellers_data = []
        total_day1 = 0
        total_day2 = 0
        total_day3 = 0
        unique_violators = len(grouped_tracked)  # Number of unique violators

        with get_db() as conn:
            cursor = conn.cursor()
            
            for seller_name, violations_list in grouped_tracked.items():
                contact_info = get_seller_contact(seller_name)

                # Process each product violation
                products = []
                for v in violations_list:
                    # Determine day status
                    if v['days_active'] == 0:
                        day_status = 'DAY_1'
                        total_day1 += 1
                    elif v['days_active'] == 1:
                        day_status = 'DAY_2'
                        total_day2 += 1
                    else:  # days_active >= 2
                        day_status = 'DAY_3'
                        total_day3 += 1

                    products.append({
                        'id': v['id'],
                        'sku': v['sku'],
                        'description': v['product_description'],
                        'current_price': v['current_price'],
                        'map_price': v['map_price'],
                        'first_detected': v['first_detected_date'],
                        'days_active': v['days_active'],
                        'day_status': day_status,
                        'first_email_sent': bool(v['first_email_sent_date']),
                        'second_email_sent': bool(v['second_email_sent_date']),
                        'pending_approval': bool(v.get('pending_approval', 0)),
                        'in_dns': bool(v.get('dns_added_date')),
                        'seller_link': v['seller_link']
                    })

                # Check if ANY product in this seller has pending_approval
                has_pending = any(p['pending_approval'] for p in products)
                has_in_dns = any(p['in_dns'] for p in products)

                # Get email tracking status for this seller
                cursor.execute("""
                    SELECT 
                        COUNT(CASE WHEN first_email_sent_date IS NOT NULL THEN 1 END) as first_emails_sent,
                        COUNT(CASE WHEN second_email_sent_date IS NOT NULL THEN 1 END) as second_emails_sent,
                        MAX(first_email_sent_date) as first_email_date,
                        MAX(second_email_sent_date) as second_email_date,
                        MAX(dns_added_date) as dns_added_date
                    FROM violations 
                    WHERE seller_name = ? AND status = 'ACTIVE'
                """, (seller_name,))
                
                tracking_data = cursor.fetchone()

                sellers_data.append({
                    'name': seller_name,
                    'contact': contact_info,
                    'products': products,
                    'pending_approval': has_pending,
                    'in_dns': has_in_dns,
                    'first_emails_sent': tracking_data[0] or 0,
                    'second_emails_sent': tracking_data[1] or 0,
                    'first_email_date': tracking_data[2],
                    'second_email_date': tracking_data[3],
                    'dns_added_date': tracking_data[4]
                })



        return jsonify({
            'success': True,
            'tracking_enabled': True,
            'total_rows': total_rows,
            'total_active_violations': len(included_violations),
            'unique_violators': unique_violators,
            'day_1_count': total_day1,
            'day_2_count': total_day2,
            'day_3_count': total_day3,
            'sellers': sellers_data,
            'uploaded_filename': file.filename,
            'upload_date': date.today().isoformat(),
            'message': f'Tracker updated: {total_day1} new, {total_day2} at 24h, {total_day3} at 48h+'
        })

    except Exception as e:
        print(f"ERROR in /upload: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/get-email-content/<filename>')
def get_email_content(filename):
    """Get email content as JSON for clipboard copy with HTML format"""
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({'error': f'File not found: {filename}'}), 404
        
        # Try to read with UTF-8 first, then fallback to other encodings
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                full_content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    full_content = f.read()
            except:
                with open(file_path, 'r', encoding='cp1252') as f:
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
        return jsonify({'error': f'Error reading file: {str(e)}'}), 500

@app.route('/verify-data/<filename>')
def verify_data(filename):
    """Get detailed verification data for a seller"""
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # We need to get the original data - this is a simplified version
        # In a real implementation, you'd store the violation data temporarily
        return jsonify({
            'message': 'Verification endpoint - implementation depends on data storage strategy'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

@app.route('/api/mark-email', methods=['POST'])
def mark_email_sent():
    """Mark email as sent for a violation"""
    try:
        data = request.json
        violation_id = data.get('violation_id')
        email_type = data.get('email_type')  # 'first' or 'second'

        with get_db() as conn:
            cursor = conn.cursor()
            if email_type == 'first':
                cursor.execute('UPDATE violations SET first_email_sent_date = date("now") WHERE id = ?', (violation_id,))
            elif email_type == 'second':
                cursor.execute('UPDATE violations SET second_email_sent_date = date("now") WHERE id = ?', (violation_id,))

        return create_success_response()
    except Exception as e:
        return create_error_response(str(e))

@app.route('/api/mark-all-emails', methods=['POST'])
def mark_all_emails_sent():
    """Mark all emails as sent for a seller by day"""
    try:
        data = request.json
        seller_name = data.get('seller_name')
        day = data.get('day')  # 0 for DAY_1, 1 for DAY_2
        

        with get_db() as conn:
            cursor = conn.cursor()
            rows_affected = 0
            
            if day == 0:
                # Mark all DAY 1 violations as first email sent
                cursor.execute('''
                    UPDATE violations
                    SET first_email_sent_date = date("now")
                    WHERE seller_name = ? AND days_active = 0 AND status = 'ACTIVE'
                ''', (seller_name,))
                rows_affected = cursor.rowcount
                
            elif day == 1:
                # Mark all DAY 2 violations as second email sent
                cursor.execute('''
                    UPDATE violations
                    SET second_email_sent_date = date("now")
                    WHERE seller_name = ? AND days_active = 1 AND status = 'ACTIVE'
                ''', (seller_name,))
                rows_affected = cursor.rowcount
            else:
                return jsonify({'error': f'Invalid day value: {day}'}), 400
            
            conn.commit()

        return jsonify({'success': True, 'rows_affected': rows_affected})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mark-dns', methods=['POST'])
def mark_violation_dns():
    """Mark individual violation as added to DNS"""
    try:
        data = request.json
        violation_id = data.get('violation_id')

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE violations SET dns_added_date = date("now") WHERE id = ?', (violation_id,))

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tracker-violations', methods=['GET'])
def get_tracker_violations():
    """Get all violations from tracker for management"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            violations = cursor.execute('''
                SELECT * FROM violations
                ORDER BY status, seller_name, days_active DESC
            ''').fetchall()

        violations_list = [dict(v) for v in violations]
        return jsonify({'success': True, 'violations': violations_list})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete-violation', methods=['POST'])
def delete_violation():
    """Delete violation from tracker"""
    try:
        data = request.json
        violation_id = data.get('violation_id')

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM violations WHERE id = ?', (violation_id,))

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/send-to-boss', methods=['POST'])
def send_to_boss():
    """Mark violations as pending approval (sent to Daniel)"""
    try:
        data = request.json
        seller_name = data.get('seller_name')

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE violations
                SET pending_approval = 1
                WHERE seller_name = ? AND days_active >= 2 AND status = 'ACTIVE'
            ''', (seller_name,))
            conn.commit()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/approve-dns', methods=['POST'])
def approve_dns():
    """Approve and add to DNS (boss approved)"""
    try:
        data = request.json
        seller_name = data.get('seller_name')

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE violations
                SET dns_added_date = date("now"), pending_approval = 0
                WHERE seller_name = ? AND pending_approval = 1 AND status = 'ACTIVE'
            ''', (seller_name,))
            conn.commit()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reject-dns', methods=['POST'])
def reject_dns():
    """Reject DNS addition (boss rejected) or remove from DNS"""
    try:
        data = request.json
        seller_name = data.get('seller_name')

        with get_db() as conn:
            cursor = conn.cursor()
            # Reset both pending_approval and dns_added_date
            cursor.execute('''
                UPDATE violations
                SET pending_approval = 0, dns_added_date = NULL
                WHERE seller_name = ? AND status = 'ACTIVE'
            ''', (seller_name,))
            conn.commit()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-current-violations', methods=['GET'])
def get_current_violations():
    """Get current violations without re-processing file"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            violations = cursor.execute('''
                SELECT * FROM violations
                WHERE status = 'ACTIVE'
                ORDER BY seller_name, days_active DESC
            ''').fetchall()

        # Group by seller (same logic as /upload)
        grouped = {}
        for v in violations:
            seller = v['seller_name']
            if seller not in grouped:
                grouped[seller] = []
            grouped[seller].append(dict(v))

        # Build sellers data
        sellers_data = []
        total_day1 = total_day2 = total_day3 = 0
        total_active_violations = 0
        unique_violators = len(grouped)  # Número de violadores únicos

        with get_db() as conn:
            cursor = conn.cursor()
            
            for seller_name, violations_list in grouped.items():
                contact_info = get_seller_contact(seller_name)

                products = []
                for v in violations_list:
                    total_active_violations += 1  # Contar violaciones totales
                    # Determine day status
                    if v['days_active'] == 0:
                        day_status = 'DAY_1'
                        total_day1 += 1
                    elif v['days_active'] == 1:
                        day_status = 'DAY_2'
                        total_day2 += 1
                    else:
                        day_status = 'DAY_3'
                        total_day3 += 1

                    products.append({
                        'id': v['id'],
                        'sku': v['sku'],
                        'description': v['product_description'],
                        'current_price': v['current_price'],
                        'map_price': v['map_price'],
                        'first_detected': v['first_detected_date'],
                        'days_active': v['days_active'],
                        'day_status': day_status,
                        'first_email_sent': bool(v['first_email_sent_date']),
                        'second_email_sent': bool(v['second_email_sent_date']),
                        'pending_approval': bool(v.get('pending_approval', 0)),
                        'in_dns': bool(v.get('dns_added_date')),
                        'seller_link': v['seller_link']
                    })

                has_pending = any(p['pending_approval'] for p in products)
                has_in_dns = any(p['in_dns'] for p in products)

                # Get email tracking status for this seller
                cursor.execute("""
                    SELECT 
                        COUNT(CASE WHEN first_email_sent_date IS NOT NULL THEN 1 END) as first_emails_sent,
                        COUNT(CASE WHEN second_email_sent_date IS NOT NULL THEN 1 END) as second_emails_sent,
                        MAX(first_email_sent_date) as first_email_date,
                        MAX(second_email_sent_date) as second_email_date,
                        MAX(dns_added_date) as dns_added_date
                    FROM violations 
                    WHERE seller_name = ? AND status = 'ACTIVE'
                """, (seller_name,))
                
                tracking_data = cursor.fetchone()

                sellers_data.append({
                    'name': seller_name,
                    'contact': contact_info,
                    'products': products,
                    'pending_approval': has_pending,
                    'in_dns': has_in_dns,
                    'first_emails_sent': tracking_data[0] or 0,
                    'second_emails_sent': tracking_data[1] or 0,
                    'first_email_date': tracking_data[2],
                    'second_email_date': tracking_data[3],
                    'dns_added_date': tracking_data[4]
                })

        return jsonify({
            'success': True,
            'tracking_enabled': True,
            'total_active_violations': total_active_violations,
            'unique_violators': unique_violators,
            'day_1_count': total_day1,
            'day_2_count': total_day2,
            'day_3_count': total_day3,
            'sellers': sellers_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export-tracker', methods=['GET'])
def export_tracker():
    """Export tracker to CSV"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            violations = cursor.execute('SELECT * FROM violations').fetchall()

        # Create CSV in memory
        output = io.StringIO()
        if violations:
            headers = violations[0].keys()
            output.write(','.join(headers) + '\n')
            for v in violations:
                output.write(','.join(str(v[h]) for h in headers) + '\n')

        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'violations_tracker_{datetime.now().strftime("%Y%m%d")}.csv'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-email-by-day/<path:seller_name>/<int:day>', methods=['GET'])
def get_email_by_day(seller_name, day):
    """Generate email for specific seller filtered by day status"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            violations = cursor.execute('''
                SELECT * FROM violations
                WHERE seller_name = ? AND days_active = ? AND status = 'ACTIVE'
            ''', (seller_name, day)).fetchall()

        if not violations:
            return jsonify({'error': 'No violations found'}), 404

        violations_list = [dict(v) for v in violations]

        # Determine email type and build body based on day
        if day == 0:
            # First Warning (Day 1)
            subject = f"IMMEDIATE ACTION REQUIRED - Glen Dimplex MAP Violation ({len(violations_list)} Product{'s' if len(violations_list) > 1 else ''})"
            warning_text = "first warning"

            # Build product list
            product_list_html = []
            for v in violations_list:
                map_html = f"<span style='font-size:15px; font-weight:700;'>${v['map_price']:.2f}</span>"
                current_html = f"<span style='font-size:16px; font-weight:800; color:#e53e3e;'>${v['current_price']:.2f}</span>"
                product_html = f"<li><strong>SKU {v['sku']}</strong> ({v['product_description']})<br>"
                product_html += f"<strong>MAP:</strong> {map_html} &nbsp;|&nbsp; <strong>Your Price:</strong> {current_html}"
                if v['seller_link'] and v['seller_link'] != 'N/A':
                    product_html += f"<br><strong>Product Link:</strong> <a href='{v['seller_link']}'>{v['seller_link']}</a>"
                product_html += "</li>"
                product_list_html.append(product_html)

            products_html = "<ul>" + "".join(product_list_html) + "</ul>"

            body = f"""<div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
<p>Hello,</p>

<p>Your company is in violation of <strong>Glen Dimplex Americas Minimum Advertised Price (MAP) Policy</strong>.</p>

<p>This is your <strong>{warning_text}</strong> for the following product(s):</p>

{products_html}

<p>Per our MAP policy, you are required to update the pricing in line with our MAP policy <strong style='color: #c53030;'>within 24 hours</strong>. If this violation is not corrected, GDA reserves the right to refuse purchase orders, stop future shipments, and/or suspend accounts at our discretion which may or may not be permanent.</p>

<p>Please note that we have had a price change effective from <strong>October 1st, 2025</strong>, and the updated price lists have been provided to your distributors.</p>

<p>If you have any questions about this MAP violation, please respond directly to this email. If you are not the correct person to receive this notice, please reply with the name, title, and contact information of the correct individual.</p>

<p>Sincerely,<br>
<strong>Glen Dimplex Americas MAP Enforcement Team</strong></p>
</div>"""

        elif day == 1:
            # Second Warning (Day 2) - Follow-up Notice
            subject = f"Glen Dimplex MAP Policy - Second Notice ({len(violations_list)} Product{'s' if len(violations_list) > 1 else ''})"

            # Build product list
            product_list_html = []
            for v in violations_list:
                map_html = f"<span style='font-size:15px; font-weight:700;'>${v['map_price']:.2f}</span>"
                current_html = f"<span style='font-size:16px; font-weight:800; color:#e53e3e;'>${v['current_price']:.2f}</span>"
                product_html = f"<li><strong>SKU {v['sku']}</strong> ({v['product_description']})<br>"
                product_html += f"<strong>MAP:</strong> {map_html} &nbsp;|&nbsp; <strong>Your Price:</strong> {current_html}"
                if v['seller_link'] and v['seller_link'] != 'N/A':
                    product_html += f"<br><strong>Product Link:</strong> <a href='{v['seller_link']}'>{v['seller_link']}</a>"
                product_html += "</li>"
                product_list_html.append(product_html)

            products_html = "<ul>" + "".join(product_list_html) + "</ul>"

            body = f"""<div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
<p>Hello,</p>

<p>We wanted to follow up on our previous communication regarding <strong>Glen Dimplex Americas Minimum Advertised Price (MAP) Policy</strong> compliance.</p>

<p><strong style='font-size: 16px;'>We have identified that the following product(s) remain in violation of our MAP policy:</strong></p>

{products_html}

<p><strong>Action Required:</strong> To maintain your account in good standing, please correct these pricing violations <strong>within the next 24 hours</strong>. 

<p>We understand that pricing adjustments may take time to implement, and we appreciate your cooperation in maintaining MAP compliance. This helps ensure fair competition among all our retail partners.</p>

<p>Per our MAP policy, continued non-compliance may result in account restrictions. GDA reserves the right to refuse purchase orders, stop future shipments, and/or suspend accounts at our discretion to maintain policy integrity.</p>

<p>Please note that we have had a price change effective from <strong>October 1st, 2025</strong>, and the updated price lists have been provided to your distributors.</p>

<p>We value our partnership and hope to resolve this matter promptly. If you have any questions about this MAP violation or need assistance with compliance, please respond directly to this email.</p>

<p>If you are not the correct person to receive this notice, please reply with the name, title, and contact information of the appropriate individual.</p>

<p>Thank you for your attention to this matter.</p>

<p>Sincerely,<br>
<strong>Glen Dimplex Americas MAP Enforcement Team</strong></p>
</div>"""
        else:
            return jsonify({'error': 'Day 3+ should not generate emails'}), 400

        return jsonify({'success': True, 'subject': subject, 'body': body})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mark-first-email/<seller_name>', methods=['POST'])
def mark_first_email(seller_name):
    """Mark Day 1 emails as sent for a seller"""
    try:
        conn = sqlite3.connect('violations_tracker.db')
        cursor = conn.cursor()
        
        current_date = datetime.now().isoformat()
        
        cursor.execute("""
            UPDATE violations 
            SET first_email_sent_date = ?
            WHERE seller_name = ? AND first_email_sent_date IS NULL
        """, (current_date, seller_name))
        
        rows_updated = cursor.rowcount
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': f'First email marked as sent for {rows_updated} products'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mark-second-email/<seller_name>', methods=['POST'])
def mark_second_email(seller_name):
    """Mark Day 2 emails as sent for a seller"""
    try:
        conn = sqlite3.connect('violations_tracker.db')
        cursor = conn.cursor()
        
        current_date = datetime.now().isoformat()
        
        cursor.execute("""
            UPDATE violations 
            SET second_email_sent_date = ?
            WHERE seller_name = ? AND second_email_sent_date IS NULL
        """, (current_date, seller_name))
        
        rows_updated = cursor.rowcount
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': f'Second email marked as sent for {rows_updated} products'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/revert-first-email/<seller_name>', methods=['POST'])
def revert_first_email(seller_name):
    """Revert Day 1 email status for a seller"""
    try:
        conn = sqlite3.connect('violations_tracker.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE violations 
            SET first_email_sent_date = NULL
            WHERE seller_name = ? AND first_email_sent_date IS NOT NULL
        """, (seller_name,))
        
        rows_updated = cursor.rowcount
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': f'First email reverted for {rows_updated} products'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/revert-second-email/<seller_name>', methods=['POST'])
def revert_second_email(seller_name):
    """Revert Day 2 email status for a seller"""
    try:
        conn = sqlite3.connect('violations_tracker.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE violations 
            SET second_email_sent_date = NULL
            WHERE seller_name = ? AND second_email_sent_date IS NOT NULL
        """, (seller_name,))
        
        rows_updated = cursor.rowcount
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': f'Second email reverted for {rows_updated} products'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mark-dns-added/<seller_name>', methods=['POST'])
def mark_dns_added(seller_name):
    """Mark seller as added to DNS (Day 3+ final action)"""
    try:
        conn = sqlite3.connect('violations_tracker.db')
        cursor = conn.cursor()
        
        current_date = datetime.now().isoformat()
        
        cursor.execute("""
            UPDATE violations 
            SET in_dns = 1, dns_added_date = ?, pending_approval = 0
            WHERE seller_name = ? AND in_dns = 0
        """, (current_date, seller_name))
        
        rows_updated = cursor.rowcount
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': f'DNS added for {rows_updated} products'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-email-status/<seller_name>')
def get_email_status(seller_name):
    """Get email tracking status for a seller"""
    try:
        conn = sqlite3.connect('violations_tracker.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_products,
                SUM(first_email_sent) as first_emails_sent,
                SUM(second_email_sent) as second_emails_sent,
                SUM(in_dns) as in_dns_count,
                MAX(first_email_sent_date) as last_first_email_date,
                MAX(second_email_sent_date) as last_second_email_date,
                MAX(dns_added_date) as dns_added_date
            FROM violations 
            WHERE seller_name = ? AND status = 'ACTIVE'
        """, (seller_name,))
        
        result = cursor.fetchone()
        conn.close()
        
        return jsonify({
            'total_products': result[0],
            'first_emails_sent': result[1],
            'second_emails_sent': result[2], 
            'in_dns_count': result[3],
            'last_first_email_date': result[4],
            'last_second_email_date': result[5],
            'dns_added_date': result[6]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
    print("=" * 80)
    print("MAP VIOLATION EMAIL GENERATOR")
    print("=" * 80)
    print("\nStarting web server...")
    print("\nPress CTRL+C to stop the server")
    print("=" * 80)
    app.run(debug=True, host='127.0.0.1', port=5000)
