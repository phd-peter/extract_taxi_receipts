# Product Overview

## 🚕 택시 영수증 자동 추출 시스템

A Korean taxi receipt data extraction tool powered by OpenAI GPT-4 Vision API.

### Core Purpose
Automatically extract structured data from Korean taxi receipt images (front and back) and export to CSV format for expense management and accounting purposes.

### Key Features
- **Dual-side Processing**: Handles both front (transaction info) and back (passenger info) of receipts
- **Batch Processing**: Process multiple receipt pairs simultaneously
- **Team Member Recognition**: Recognizes specific team member names from receipts
- **CSV Export**: Structured data output with consistent formatting
- **Multi-interface Support**: CLI and GUI (PyQt5) interfaces available

### Target Users
- Internal company teams for expense tracking
- Accounting departments processing taxi receipts
- Employees submitting taxi expense claims

### Data Extracted
- **paid_at**: Transaction timestamp (YYYY-MM-DD HH:MM format)
- **name**: Passenger name (from predefined team member list)
- **route**: Trip route or purpose (회사-집, 야근택시비, etc.)
- **fare**: Total fare amount in KRW

### Recognized Team Members
최홍영, 박다혜, 박상현, 김민주, 최윤선, 김익현, 장수현, 이한울, 김호연, 박성진