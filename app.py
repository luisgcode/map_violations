import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import re
import io
import zipfile

# Configure the page
st.set_page_config(
    page_title="MAP Violation Email Generator",
    page_icon="📧",
    layout="wide"
)

def read_violations(uploaded_file):
    """
    Read Excel file and filter only rows with MAP violations.
    A violation occurs when price_difference < 0
    """
    df = pd.read_excel(uploaded_file)

    # Filter only violations (price_difference < 0)
    violations = df[df['price_difference'] < 0].copy()

    return violations, len(df)

def group_by_seller(violations_df):
    """
    Group violations by seller.
    Returns a dictionary: {seller_name: DataFrame_of_violations}
    """
    grouped = {}

    for seller in violations_df['sellers'].unique():
        seller_violations = violations_df[violations_df['sellers'] == seller]
        grouped[seller] = seller_violations

    return grouped

def generate_email_single_product(seller_name, product_row):
    """
    Generate email for a single product violation.
    """
    sku = product_row['SAP Material']
    description = product_row['Description']
    map_price = product_row['U.S. MAP']
    current_price = product_row['prices']

    # Create subject
    subject = "Subject: IMMEDIATE ACTION REQUIRED - Glen Dimplex MAP Violation (1 Product)"

    # Create body
    body = f"""Hello,
Your company is in violation of Glen Dimplex Americas Minimum Advertised Price (MAP) Policy. Dimplex SKU {sku} has a MAP price of ${map_price:.2f}, and you are currently selling below this at ${current_price:.2f}.

Per our MAP policy, you are required to update the pricing in line with our MAP policy within 24 hours. If this violation is not corrected, GDA reserves the right to refuse purchase orders, stop future shipments, and/or suspend accounts is at our discretion which may or may not be permanent.

Please note that we have had a price change effective from October 1st, 2025, and the updated price lists have been provided to your distributors.

[insert screenshot of online MAP violation as backup/proof]
[insert link here with the violation]

If you have any questions about this MAP violation, please respond directly to this email. If you are not the correct person to receive this notice, please reply with the name, title, and contact information of the correct individual.

Sincerely,
Glen Dimplex Americas MAP Enforcement Team"""

    # Combine subject and body
    email = f"{subject}\n\n{body}"

    return email

def generate_email_multiple_products(seller_name, products_df):
    """
    Generate email for multiple product violations.
    """
    num_products = len(products_df)

    # Create subject
    subject = f"Subject: IMMEDIATE ACTION REQUIRED - Glen Dimplex MAP Violations ({num_products} Products)"

    # Build product list
    product_list = []
    for idx, row in products_df.iterrows():
        sku = row['SAP Material']
        description = row['Description']
        map_price = row['U.S. MAP']
        current_price = row['prices']

        product_list.append(f"- SKU {sku} ({description}): MAP ${map_price:.2f}, Your Price: ${current_price:.2f}")

    products_text = "\n".join(product_list)

    # Create body
    body = f"""Hello,
Your company is in violation of Glen Dimplex Americas Minimum Advertised Price (MAP) Policy. The following Dimplex SKUs are currently being sold below MAP:

{products_text}

Per our MAP policy, you are required to update the pricing in line with our MAP policy within 24 hours. If this violation is not corrected, GDA reserves the right to refuse purchase orders, stop future shipments, and/or suspend accounts is at our discretion which may or may not be permanent.

Please note that we have had a price change effective from October 1st, 2025, and the updated price lists have been provided to your distributors.

[insert screenshot of online MAP violation as backup/proof]
[insert link here with the violation]

If you have any questions about this MAP violation, please respond directly to this email. If you are not the correct person to receive this notice, please reply with the name, title, and contact information of the correct individual.

Sincerely,
Glen Dimplex Americas MAP Enforcement Team"""

    # Combine subject and body
    email = f"{subject}\n\n{body}"

    return email

def clean_filename(seller_name):
    """
    Clean seller name to create a valid filename.
    """
    # Replace spaces with underscores
    cleaned = seller_name.replace(' ', '_')
    # Remove special characters
    cleaned = re.sub(r'[^\w\-_]', '', cleaned)
    return cleaned

def generate_emails(grouped_violations):
    """
    Generate email content for all sellers.
    Returns a dictionary: {filename: email_content}
    """
    emails = {}

    for seller_name, violations_df in grouped_violations.items():
        num_violations = len(violations_df)

        # Generate appropriate email based on number of violations
        if num_violations == 1:
            email_content = generate_email_single_product(
                seller_name,
                violations_df.iloc[0]
            )
        else:
            email_content = generate_email_multiple_products(
                seller_name,
                violations_df
            )

        # Create filename
        filename = f"email_{clean_filename(seller_name)}.txt"
        emails[filename] = email_content

    return emails

def create_zip(emails_dict):
    """
    Create a ZIP file containing all email files.
    Returns a BytesIO object with the ZIP content.
    """
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename, content in emails_dict.items():
            zip_file.writestr(filename, content)

    zip_buffer.seek(0)
    return zip_buffer

# Main App UI
st.title("📧 MAP Violation Email Generator")
st.markdown("---")

st.markdown("""
### How to use:
1. Upload your daily MAP Excel file
2. System will automatically detect violations
3. Download individual email files or all at once
4. Copy and paste into Outlook
""")

st.markdown("---")

# File uploader
uploaded_file = st.file_uploader(
    "Upload MAP Excel File",
    type=['xlsx', 'xls'],
    help="Upload the daily MAP file (e.g., map-base.xlsx)"
)

if uploaded_file is not None:
    try:
        # Process the file
        with st.spinner("Analyzing Excel file..."):
            violations_df, total_rows = read_violations(uploaded_file)

        # Display summary
        st.success(f"✓ File processed successfully!")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Rows", total_rows)
        with col2:
            st.metric("Total Violations", len(violations_df))
        with col3:
            if len(violations_df) > 0:
                grouped = group_by_seller(violations_df)
                st.metric("Sellers with Violations", len(grouped))
            else:
                st.metric("Sellers with Violations", 0)

        if len(violations_df) == 0:
            st.info("🎉 No violations found! All sellers are complying with MAP policy.")
        else:
            st.markdown("---")

            # Generate emails
            with st.spinner("Generating email files..."):
                grouped_violations = group_by_seller(violations_df)
                emails = generate_emails(grouped_violations)

            st.success(f"✓ Generated {len(emails)} email files!")

            # Show download options
            st.markdown("### Download Options")

            # Option 1: Download all as ZIP
            st.markdown("#### Download All Files")
            zip_buffer = create_zip(emails)
            st.download_button(
                label="📦 Download All Emails (ZIP)",
                data=zip_buffer,
                file_name=f"map_violation_emails_{datetime.now().strftime('%Y%m%d')}.zip",
                mime="application/zip",
                use_container_width=True
            )

            st.markdown("---")

            # Option 2: Download individual files
            st.markdown("#### Download Individual Files")

            # Create columns for better layout
            num_cols = 2
            cols = st.columns(num_cols)

            for idx, (filename, content) in enumerate(emails.items()):
                col = cols[idx % num_cols]

                # Extract seller name from filename
                seller_name = filename.replace('email_', '').replace('.txt', '').replace('_', ' ')

                # Count violations for this seller
                num_violations = len(grouped_violations[list(grouped_violations.keys())[idx]])

                with col:
                    st.download_button(
                        label=f"📄 {seller_name} ({num_violations} violation{'s' if num_violations > 1 else ''})",
                        data=content,
                        file_name=filename,
                        mime="text/plain",
                        use_container_width=True
                    )

            st.markdown("---")

            # Show violation details
            with st.expander("📊 View Violation Details"):
                for seller_name, seller_violations in grouped_violations.items():
                    st.markdown(f"**{seller_name}** - {len(seller_violations)} violation(s)")

                    # Display table with violation details
                    display_cols = ['SAP Material', 'Description', 'U.S. MAP', 'prices', 'price_difference']
                    st.dataframe(
                        seller_violations[display_cols],
                        use_container_width=True,
                        hide_index=True
                    )
                    st.markdown("---")

    except Exception as e:
        st.error(f"❌ Error processing file: {str(e)}")
        st.markdown("**Please make sure your Excel file has the following columns:**")
        st.markdown("- sellers")
        st.markdown("- prices")
        st.markdown("- U.S. MAP")
        st.markdown("- price_difference")
        st.markdown("- Description")
        st.markdown("- SAP Material")

else:
    st.info("👆 Please upload an Excel file to get started")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <small>MAP Violation Email Generator | Glen Dimplex Americas</small>
</div>
""", unsafe_allow_html=True)
