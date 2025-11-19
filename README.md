# MAP Violations Dashboard

## 🎯 Overview
Advanced MAP (Minimum Advertised Price) violation tracking and management system with automated email generation, DNS blocking capabilities, and comprehensive violation lifecycle management.

## ✨ Key Features

### 📊 **Violation Management**
- **Multi-day tracking**: Day 1 (New), Day 2 (24h), Day 3+ (DNS eligible)
- **Automated escalation**: Progressive enforcement with color-coded severity
- **Real-time monitoring**: Live updates of violation status and seller compliance

### 🚦 **Severity System**
- 🟢 **Green**: Day 1 violations (new detections)
- 🟡 **Yellow**: Day 2 & Day 3+ violations (persistent offenders)  
- 🟣 **Pink**: Pending approval violations (sent to management)
- 🔴 **Red**: DNS blocked sellers (maximum penalty)

### 🔒 **DNS Management**
- **Automated blocking**: One-click DNS addition for repeat offenders
- **Approval workflow**: Management approval system for DNS decisions
- **Visual indicators**: Clear DNS status display on seller cards
- **Reversible actions**: Full DNS management with approve/reject capabilities

### 📧 **Email Automation**
- **Template-based emails**: Professional violation notifications
- **Multi-stage workflow**: First notice, second notice, final warning
- **Contact integration**: Automatic seller contact information lookup
- **Tracking system**: Full email send history and status tracking

### 🎨 **Modern UI/UX**
- **Optimized CSS**: Clean, responsive design with direct hex color codes
- **Performance optimized**: Removed duplicate code and unused styles
- **Mobile responsive**: Works seamlessly across all device sizes
- **Intuitive interface**: Color-coded violations with clear action buttons

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Flask 3.0.0
- SQLite (included)

### Installation
```bash
# Clone repository
git clone https://github.com/luisgcode/map_violations.git
cd map_violations

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run application
python app_flask.py
```

### Usage
1. **Upload Excel file** with violation data
2. **Review violations** organized by seller and severity
3. **Send notifications** using automated email templates
4. **Manage escalation** through approval workflow
5. **Apply DNS blocks** for repeat offenders

## 📁 Project Structure
```
map_violations/
├── app_flask.py              # Main Flask application
├── static/css/               # Optimized stylesheets
│   ├── main.css             # Application-specific styles
│   ├── components.css       # Reusable UI components
│   ├── base.css            # Typography and base styles
│   └── layout.css          # Layout utilities
├── templates/
│   └── index.html          # Main dashboard interface
├── uploads/                # Excel file storage
├── output/                 # Generated email files
├── violations_tracker.db   # SQLite database
├── seller_contacts.txt     # Contact information
├── excluded_sellers.txt    # Exclusion list
└── MAP-mail-template      # Email templates

```

## 🗄️ Database Schema
```sql
violations (
    id INTEGER PRIMARY KEY,
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
    dns_added_date TEXT DEFAULT NULL
)
```

## 🔧 API Endpoints

### Violation Management
- `POST /upload` - Upload and process Excel files
- `GET /api/get-current-violations` - Retrieve active violations
- `POST /api/delete-violation` - Remove violation records

### Email System  
- `POST /api/mark-email` - Mark emails as sent (Day 1/2)
- `POST /api/mark-all-emails` - Bulk email status updates
- `GET /get-email-content/<filename>` - Retrieve email templates

### DNS Management
- `POST /api/send-to-boss` - Submit for management approval
- `POST /api/approve-dns` - Approve and add to DNS
- `POST /api/reject-dns` - Reject DNS addition
- `POST /api/mark-dns` - Mark individual violation as DNS

### Data Export
- `GET /download/<filename>` - Download individual email
- `GET /download-all` - Bulk download all emails
- `GET /api/export-tracker` - Export violation tracking data

## 🎨 CSS Architecture

### Optimized Design System
- **Direct hex colors**: No CSS variables for maximum performance
- **Modular structure**: Separated concerns across CSS files
- **Removed duplicates**: Eliminated 600+ lines of redundant code
- **Mobile-first**: Responsive grid system with auto-fit layouts

### Color Palette
- `#254167` - Primary background
- `#2B4A73` - Surface elements  
- `#1F3A5F` - Card backgrounds
- `#E6EEF9` - Primary text
- `#4CC879` - Success/Day 1 violations
- `#F59E0B` - Warning/Day 2-3 violations
- `#EF4444` - Danger/DNS blocked
- `#E39CCB` - Pending approval

## 🔄 Violation Lifecycle

1. **Detection** → New violation uploaded (Day 1, Green)
2. **Persistence** → 24h+ active (Day 2, Yellow) 
3. **Escalation** → 72h+ active (Day 3+, Yellow)
4. **Management Review** → Sent to boss (Pending, Pink)
5. **DNS Blocking** → Approved for blocking (DNS, Red)

## 🚨 Error Handling
- **Database integrity**: Automatic conflict resolution
- **File validation**: Excel format and structure verification  
- **State consistency**: Pending/DNS status validation
- **Graceful failures**: User-friendly error messages

## 📈 Performance Optimizations
- **CSS reduction**: 33% smaller main.css, 93% smaller layout.css
- **Database efficiency**: Optimized queries with proper indexing
- **Memory management**: Efficient file processing for large datasets
- **Caching**: Static asset optimization

## 🤝 Contributing
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License
This project is proprietary software developed for Glen Dimplex MAP violation management.

## 👨‍💻 Author
**Luis Guaiquirian** - Marketing Team, Glen Dimplex  
*MAP Violation Management System*

---
*Last updated: November 19, 2025*



A professional Flask web application for processing MAP (Minimum Advertised Price) violations and generating automated email reports. Built with Luis GCode Design System.



## ⚡ Quick StartA professional Flask web application for processing MAP (Minimum Advertised Price) violations and generating automated email reports. Built with Luis GCode Style design system.System to detect MAP violations and manage seller emails.



```bash

.\start.ps1        # Windows - Just run this

```## ⚡ Quick Start## 🚀 How to start



## 🚀 How to Start



### Prerequisites### Prerequisites```bash

- Python 3.8+

- Virtual environment (recommended)- Python 3.8+.\start.ps1        # Just run this



### Setup Steps- Virtual environment (recommended)```



1. **Clone and Navigate**

   ```bash

   cd map_violations### InstallationThen go to: http://localhost:5000

   ```

```bash

2. **Create Virtual Environment**

   ```bash# Clone and navigate to project## 📋 What it does

   python -m venv .venv

   .\.venv\Scripts\activate    # Windowscd map_violations

   source .venv/bin/activate   # Linux/Mac

   ```1. **Upload Excel** with price violations



3. **Install Dependencies**# Create and activate virtual environment2. **See all sellers** with contacts and violations

   ```bash

   pip install -r requirements.txtpython -m venv .venv3. **Copy emails** ready to send

   ```

.venv\Scripts\activate  # Windows4. **Track sent emails** (first and second email)

4. **Run Application**

   ```bash# source .venv/bin/activate  # Linux/Mac5. **Mark for DNS** when they don't respond

   python app_flask.py

   ```



5. **Access Dashboard**# Install dependencies## 📁 Important files

   - Open browser: http://localhost:5000

pip install -r requirements.txt

## 📁 Project Structure

- `app_flask.py` - The main application

```

map_violations/# Start the application- `seller_contacts.txt` - Seller contacts (edit here)

├── app_flask.py              # Main Flask application

├── static/python app_flask.py- `excluded_sellers.txt` - Sellers to ignore (e.g. Amazon)

│   └── css/                  # Modular CSS Architecture

│       ├── variables.css     # Design tokens```- `violations_tracker.db` - Database (don't touch)

│       ├── base.css         # Reset & base styles

│       ├── layout.css       # Layout utilities

│       ├── components.css   # UI components

│       └── main.css         # Main entry point### Access## ⚙️ To edit contacts

├── templates/

│   └── index.html           # Main dashboard templateOpen your browser to: **http://127.0.0.1:5000**

├── uploads/                 # Excel files storage

├── output/                  # Generated email filesIn `seller_contacts.txt`:

└── violations_tracker.db    # SQLite database

```## 🚀 Features```



## 🎨 Luis GCode Design SystemSeller Name | email@example.com | 555-1234 | website



### CSS Architecture### Core Functionality```

- **Modular CSS**: 5 separate modules for maintainability

- **CSS Custom Properties**: Complete design token system- **📊 Excel Processing**: Upload and process MAP violation data**Restart Flask after changes**

- **No External Dependencies**: Pure CSS without frameworks

- **Semantic Components**: Meaningful class names- **📧 Automated Emails**: Generate professional violation notices



### Color Palette- **📋 Tracking System**: Multi-day violation tracking (Day 1, Day 2, Day 3+)## 📧 Tracking system

```css

--color-main: #0F1722        /* Deep dark blue background */- **🎯 Smart Filtering**: Automatic exclusion of configured sellers

--color-brand: #0A4F8F       /* Brand blue */

--color-accent: #1974C8      /* Interactive elements */- **📈 Analytics Dashboard**: Real-time violation metrics and insights- **Day 1**: New violations

--color-orchid: #E39CCB      /* Accent highlights */

```- **Day 2**: 24h later 



## 🔧 Features### Email Management- **Day 3+**: For DNS action



- **Excel Upload**: Drag & drop interface- **Day 1**: First notice emails for new violations

- **Real-time Processing**: Live progress updates

- **Violation Detection**: Day 1, 2, 3 tracking- **Day 2**: Follow-up notices for unresolved violations  ## 🎯 Funcionalidades

- **Email Generation**: Professional email templates

- **Seller Management**: Contact information tracking- **Day 3+**: Escalation to management with DNS blocking options

- **DNS Monitoring**: Do-not-sell status tracking

- **Responsive Design**: Mobile-friendly interface- **📋 Copy to Clipboard**: One-click email copying for Outlook✅ **Implemented:**



## 📊 Dashboard Features- **✅ Progress Tracking**: Mark emails as sent with date tracking- Excel upload with drag & drop



- **Metrics Cards**: Violations summary- Automatic violation detection 

- **Two-Column Layout**: Organized seller display

- **Contact Integration**: Email and phone tracking### Business Intelligence- Day-based tracking system

- **Product Details**: SKU and pricing information

- **Status Badges**: Visual violation indicators- **📊 Violation Metrics**: Active violations, unique violators, day-wise counts- Professional email templates



## 🛠️ Technology Stack- **🔍 Data Validation**: Confidence scoring and integrity checks- Direct copy/paste to Outlook



- **Backend**: Python 3.8+ with Flask- **📱 Responsive Design**: Mobile-friendly dashboard interface- Database with history

- **Database**: SQLite

- **Frontend**: HTML5, CSS3, Vanilla JavaScript- **🎨 Professional UI**: Luis GCode Style system with modern aesthetics- Corporate colors

- **Design**: Luis GCode Design System

- **Architecture**: Modular CSS, Component-based- Buttons to mark emails sent



## 📝 Usage## 🛠️ Technical Stack



1. **Upload Excel File**: Use the drag & drop area⭐ **Next steps:** (decide what to implement)

2. **View Metrics**: Check violation counts and summaries

3. **Review Sellers**: Browse two-column seller grid- **Backend**: Flask 3.0.0- Auto-send emails

4. **Generate Emails**: Download ready-to-send emails

5. **Track Progress**: Monitor violation status- **Data Processing**: Pandas 2.1.4- Automatic reports



## 🎯 Key Benefits- **Excel Support**: OpenPyXL 3.1.2- Notifications



- **Professional UI**: Clean, modern dark theme- **Database**: SQLite (violations tracking)- Integration with other systems

- **Scalable Architecture**: Modular CSS design

- **Fast Performance**: Lightweight, no external dependencies- **Frontend**: HTML5, CSS3 (Modular architecture)

- **Easy Maintenance**: Well-organized codebase

- **Responsive Design**: Works on all devices- **Design System**: Luis GCode Style (Component-based)---



---



**Created by Luis Guaiquirian - Marketing Team**  ## 📁 Project Structure**Created by:** Luis Guaiquirian - Glen Dimplex Americas

*Luis GCode Design System v2.0*
**License:** Internal company use only

```
map_violations/
├── app_flask.py              # Main Flask application
├── requirements.txt          # Python dependencies
├── violations_tracker.db     # SQLite database
├── static/
│   ├── styles.css           # Main stylesheet (imports modules)
│   └── css/
│       ├── _variables.css    # Design tokens & CSS variables
│       ├── _base.css        # Base styles & typography
│       ├── _components.css  # UI components (buttons, cards)
│       └── _layout.css      # Grid system & layouts
├── templates/
│   └── index.html           # Main dashboard template
├── uploads/                 # Excel file uploads
├── output/                  # Generated email files
├── excluded_sellers.txt     # Seller exclusion list
└── seller_contacts.txt      # Seller contact information
```

## 🎨 Design System

Built with **Luis GCode Style** - a professional component-based design system featuring:
- **🎯 Modular CSS Architecture**: Separate files for variables, base styles, components, and layouts
- **🎨 Professional Color Palette**: Blue-based theme with subtle pink accents
- **📱 Responsive Design**: Mobile-first approach with breakpoint system
- **⚡ Smooth Animations**: Micro-interactions and transitions
- **♿ Accessibility**: WCAG AA compliance with proper contrast ratios

## 🔧 Configuration

### Seller Exclusions
Add seller names to `excluded_sellers.txt` (one per line) to exclude from processing.

### Contacts Database  
Seller contact information is managed in `seller_contacts.txt` and the SQLite database.

### Email Templates
Email templates are dynamically generated based on violation data and day status.

## 🧩 Reusable Components

### Creator Signature Component
A floating signature component perfect for crediting work across projects:

```html
<!-- Basic usage (top-right corner) -->
<div class="creator-sign">Created by <b>Your Name</b></div>

<!-- Bottom-right corner -->
<div class="creator-sign creator-sign--bottom-right">© 2025 <b>Your Name</b></div>

<!-- Bottom-left corner -->
<div class="creator-sign creator-sign--bottom-left">Made with ❤️ by <b>Team</b></div>

<!-- Inline with content -->
<div class="creator-sign creator-sign--inline">By <b>Author</b></div>

<!-- Centered block -->
<div class="creator-sign creator-sign--centered">Created by Marketing Team - <b>Luis Guaiquirian</b></div>
```

**Component Features:**
- ✨ Floating positioned with smooth hover effects
- 📱 Responsive design (becomes inline on mobile)
- 🎨 Multiple position variants (top/bottom, left/right)
- 🔄 Consistent with Luis GCode design system
- 🚀 Easy to customize and reuse in other projects

---

**Created by Marketing Team - Luis Guaiquirian**  
*Built with ❤️ using Luis GCode Design System v2.0*