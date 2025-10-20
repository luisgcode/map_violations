import pandas as pd
from pathlib import Path
from datetime import datetime
import re

def read_violations(excel_file):
    """
    Read Excel file and filter only rows with MAP violations.
    A violation occurs when price_difference < 0
    """
    print(f"Reading Excel file: {excel_file}")
    df = pd.read_excel(excel_file)

    # Filter only violations (price_difference < 0)
    violations = df[df['price_difference'] < 0].copy()

    print(f"Total rows in file: {len(df)}")
    print(f"Total violations found: {len(violations)}")

    return violations

def group_by_seller(violations_df):
    """
    Group violations by seller.
    Returns a dictionary: {seller_name: list_of_violation_rows}
    """
    grouped = {}

    for seller in violations_df['sellers'].unique():
        seller_violations = violations_df[violations_df['sellers'] == seller]
        grouped[seller] = seller_violations

    print(f"\nViolations grouped by {len(grouped)} sellers")

    return grouped

def generate_email_single_product(seller_name, product_row, template):
    """
    Generate email for a single product violation.
    Uses the original template with placeholders filled in.
    """
    sku = product_row['SAP Material']
    description = product_row['Description']
    map_price = product_row['U.S. MAP']
    current_price = product_row['prices']

    # Read the template
    with open(template, 'r') as f:
        template_text = f.read()

    # Create subject
    subject = "Subject: IMMEDIATE ACTION REQUIRED - Glen Dimplex MAP Violation (1 Product)"

    # Adapt the body - replace placeholders
    body = template_text.replace('[Date, Product Family, Sku]', f'{datetime.now().strftime("%B %d, %Y")} - {sku}')
    body = body.replace('[insert here]', f'{sku}')
    body = body.replace('has a MAP price of [insert here]', f'has a MAP price of ${map_price:.2f}')
    body = body.replace('[insert MAP violation price here]', f'${current_price:.2f}')

    # Combine subject and body
    email = f"{subject}\n\n{body}"

    return email

def generate_email_multiple_products(seller_name, products_df, template):
    """
    Generate email for multiple product violations.
    Adapts template to plural form with a list of products.
    """
    num_products = len(products_df)

    # Read the template
    with open(template, 'r') as f:
        template_text = f.read()

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

    # Adapt the body for multiple products
    body_lines = template_text.split('\n')

    # Find the line that mentions "Dimplex SKU" and replace it with the list
    adapted_body = []
    for line in body_lines:
        if 'Dimplex SKU' in line and '[insert here]' in line:
            # Replace with plural version
            adapted_body.append("Your company is in violation of Glen Dimplex Americas Minimum Advertised Price (MAP) Policy. The following Dimplex SKUs are currently being sold below MAP:")
            adapted_body.append("")
            adapted_body.append(products_text)
        elif '[Date, Product Family, Sku]' in line:
            adapted_body.append(line.replace('[Date, Product Family, Sku]', f'{datetime.now().strftime("%B %d, %Y")} - Multiple Products'))
        else:
            adapted_body.append(line)

    body = '\n'.join(adapted_body)

    # Combine subject and body
    email = f"{subject}\n\n{body}"

    return email

def clean_filename(seller_name):
    """
    Clean seller name to create a valid filename.
    Remove special characters and spaces.
    """
    # Replace spaces with underscores
    cleaned = seller_name.replace(' ', '_')
    # Remove special characters
    cleaned = re.sub(r'[^\w\-_]', '', cleaned)
    return cleaned

def generate_output_files(grouped_violations, template, output_dir='output'):
    """
    Generate individual text files for each seller with violations.
    Each file contains the complete email ready to copy/paste.
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    print(f"\nGenerating email files in '{output_dir}/' folder...")

    files_created = []

    for seller_name, violations_df in grouped_violations.items():
        num_violations = len(violations_df)

        # Generate appropriate email based on number of violations
        if num_violations == 1:
            email_content = generate_email_single_product(
                seller_name,
                violations_df.iloc[0],
                template
            )
        else:
            email_content = generate_email_multiple_products(
                seller_name,
                violations_df,
                template
            )

        # Create filename
        filename = f"email_{clean_filename(seller_name)}.txt"
        filepath = output_path / filename

        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(email_content)

        files_created.append(filename)
        print(f"  ✓ Created: {filename} ({num_violations} violation{'s' if num_violations > 1 else ''})")

    return files_created

def main():
    """
    Main function that orchestrates the entire process.
    """
    print("=" * 80)
    print("MAP VIOLATION EMAIL GENERATOR")
    print("=" * 80)
    print()

    # Configuration
    excel_file = 'map-base.xlsx'
    template_file = 'MAP-mail-template'
    output_dir = 'output'

    # Check if files exist
    if not Path(excel_file).exists():
        print(f"ERROR: Excel file '{excel_file}' not found!")
        return

    if not Path(template_file).exists():
        print(f"ERROR: Template file '{template_file}' not found!")
        return

    # Step 1: Read violations from Excel
    violations_df = read_violations(excel_file)

    if len(violations_df) == 0:
        print("\n✓ No violations found! All sellers are complying with MAP policy.")
        return

    # Step 2: Group violations by seller
    grouped_violations = group_by_seller(violations_df)

    # Step 3: Generate output files
    files_created = generate_output_files(grouped_violations, template_file, output_dir)

    # Final summary
    print()
    print("=" * 80)
    print("PROCESS COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print(f"Total files generated: {len(files_created)}")
    print(f"Location: {Path(output_dir).absolute()}")
    print()
    print("Next steps:")
    print("1. Open the output folder")
    print("2. Open each email file")
    print("3. Copy the entire content")
    print("4. Paste into a new Outlook email")
    print("=" * 80)

if __name__ == "__main__":
    main()
