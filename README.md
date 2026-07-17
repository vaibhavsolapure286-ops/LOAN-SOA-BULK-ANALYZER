# Loan SOA Bulk Analyzer

A production-ready Python application for automated analysis of Statement of Account (SOA) PDF files for loan portfolios.

## Features

- **PDF Text Extraction**: Extracts text from PDF SOA documents using `pdfplumber`
- **Loan Information Extraction**: Automatically identifies:
  - Customer Name
  - Loan Number
  - Loan Amount
  - EMI Amount
  - Current Principal Outstanding (POS)

- **Transaction Analysis**:
  - **EMI Detection**: Identifies EMI receipts using keywords (NACH, IMPS, etc.)
  - **Bounce Detection**: Identifies bounce events and charges
  - **Late Payment Detection**: Marks EMIs paid after the 8th of the month as late

- **Risk Grading**:
  - Grade A: 0 bounces
  - Grade B: 1-2 bounces
  - Grade C: 3-5 bounces
  - Grade D: >5 bounces

- **Excel Export**: Generates comprehensive Excel reports with 4 sheets:
  - Portfolio Summary
  - Bounce Details
  - Late EMI Details
  - Individual Loan Summary

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

1. Clone the repository:
```bash
git clone https://github.com/vaibhavsolapure286-ops/loan-soa-bulk-analyzer.git
cd loan-soa-bulk-analyzer
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Quick Start

1. Place your PDF SOA files in the `input_pdfs/` directory

2. Run the analyzer:
```bash
python main.py
```

3. Check the `output/` directory for `loan_portfolio_analysis.xlsx`

### Project Structure

```
loan-soa-bulk-analyzer/
├── config.py                 # Configuration and constants
├── pdf_extractor.py          # PDF text extraction
├── transaction_analyzer.py   # Transaction analysis
├── excel_exporter.py         # Excel report generation
├── main.py                   # Main orchestrator
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── input_pdfs/              # Input PDF files (place SOAs here)
└── output/                  # Output Excel reports
```

## Module Details

### config.py
Central configuration module containing:
- Directory paths
- EMI and bounce detection keywords
- EMI due date (8th of month)
- Risk grading thresholds
- Excel sheet names

**Customization**: Edit this file to adjust keywords, due dates, or risk grades.

### pdf_extractor.py
`PDFExtractor` class handles:
- Text extraction from PDFs
- Pattern matching for loan information
- Transaction extraction from ledger

**Key Methods**:
- `extract_text_from_pdf()`: Extracts all text from PDF
- `extract_customer_name()`: Identifies customer name
- `extract_loan_number()`: Identifies loan number
- `extract_loan_amount()`: Identifies principal loan amount
- `extract_emi_amount()`: Identifies EMI amount
- `extract_current_pos()`: Identifies current outstanding balance
- `extract_transactions()`: Parses transaction lines
- `process_pdf()`: Complete single PDF analysis
- `process_all_pdfs()`: Batch process directory

### transaction_analyzer.py
`TransactionAnalyzer` class performs:
- EMI receipt detection
- Bounce event identification
- Late payment detection
- Risk grade assignment

**Key Methods**:
- `detect_emi_receipt()`: Identifies EMI transactions
- `detect_bounce()`: Identifies bounce charges
- `parse_date()`: Converts date strings to datetime objects
- `is_late_payment()`: Checks if payment exceeds due date
- `analyze_transactions()`: Complete transaction analysis
- `assign_risk_grade()`: Assigns A/B/C/D grade
- `analyze_loan_portfolio()`: Portfolio-wide analysis

### excel_exporter.py
`ExcelExporter` class creates formatted Excel reports with:
- Automatic currency formatting
- Styled headers
- Auto-adjusted column widths
- Summary calculations

**Sheets Generated**:
1. **Portfolio Summary**: Aggregate view of all loans with totals
2. **Bounce Details**: Line-by-line bounce events
3. **Late EMI Details**: Late payment transactions with days late
4. **Individual Loan Summary**: Detailed metrics per loan

### main.py
`LoanSOABulkAnalyzer` class orchestrates the entire pipeline:
1. Extracts data from all PDFs
2. Analyzes transactions
3. Exports to Excel
4. Logs summary statistics

## Configuration

### Customizing Keywords

Edit `config.py` to modify detection keywords:

```python
EMI_KEYWORDS = [
    "NACH Presented",
    "EMI Received",
    "IMPS Received",
    "Amount Received as EMI",
    # Add more keywords as needed
]

BOUNCE_KEYWORDS = [
    "Bounced Return",
    "Bounce",
    "Bouncing Charges",
    # Add more keywords as needed
]
```

### Adjusting Risk Grades

Modify the `RISK_GRADES` dictionary:

```python
RISK_GRADES = {
    "A": (0, 0),          # 0 bounces
    "B": (1, 2),          # 1-2 bounces
    "C": (3, 5),          # 3-5 bounces
    "D": (6, float("inf")), # >5 bounces
}
```

### Changing EMI Due Date

Update `EMI_DUE_DATE` in `config.py`:

```python
EMI_DUE_DATE = 8  # Change to desired date (1-31)
```

## Output Format

### Excel File Structure

**Portfolio Summary Sheet**:
| Loan Number | Customer Name | Loan Amount | EMI | Current POS | Total Bounces | Late EMI Count | Risk Grade |
|-------------|---------------|-------------|-----|-------------|---------------|----------------|------------|
| LN001 | John Doe | 500,000 | 15,000 | 250,000 | 2 | 1 | B |
| ... | ... | ... | ... | ... | ... | ... | ... |

**Bounce Details Sheet**:
| Loan Number | Customer Name | Bounce Date | Description | Amount |
|-------------|---------------|-------------|-------------|--------|
| LN001 | John Doe | 15-03-2023 | Bouncing Charges | 500 |

**Late EMI Details Sheet**:
| Loan Number | Customer Name | Payment Date | Due Date | Days Late | Description | Amount |
|-------------|---------------|--------------|----------|-----------|-------------|--------|
| LN001 | John Doe | 15-03-2023 | 08-03-2023 | 7 | EMI Received | 15,000 |

**Individual Loan Summary Sheet**:
| Loan Number | Customer Name | Loan Amount | EMI Amount | Current POS | Total EMI Paid | Total Bounces | Late EMI Count | Risk Grade | PDF Source |

## Logging

The application provides detailed logging at each stage:
- PDF extraction progress
- Transaction analysis details
- Excel export confirmation
- Summary statistics

Check console output for operation status and any warnings/errors.

## Error Handling

The application includes robust error handling:
- Invalid date format handling
- Missing field defaults to None
- PDF extraction failures logged but don't halt processing
- Transaction parsing errors skipped gracefully

## Performance

- Processes multiple PDFs in batch
- Efficient regex-based pattern matching
- Pandas-based operations for fast data transformation
- Excel export with formatting applied in single pass

## Troubleshooting

### No PDFs found
- Ensure PDF files are in the `input_pdfs/` directory
- Verify file extension is `.pdf` (lowercase)

### Missing loan information
- Check if PDF SOA format matches expected patterns
- Add custom regex patterns in `PDFExtractor` class
- Review regex patterns in `config.py` keywords

### Incorrect bounce/EMI detection
- Verify keywords match your SOA format
- Update `EMI_KEYWORDS` and `BOUNCE_KEYWORDS` in `config.py`
- Check transaction descriptions in generated report

### Excel formatting issues
- Ensure `openpyxl` is installed and up-to-date
- Verify output directory has write permissions

## Contributing

Improvements and adaptations are welcome. Common enhancements:
- Support for additional SOA formats
- OCR integration for scanned PDFs
- Database export options
- Web API interface
- Custom report templates

## License

This project is open source and available under the MIT License.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review logs for error details
3. Verify PDF format and keywords match expectations

## Version History

### v1.0.0 (2024)
- Initial release
- PDF extraction and analysis
- EMI and bounce detection
- Risk grading
- Excel export with 4 sheets
- Production-ready code

---

**Last Updated**: July 2024
**Python Version**: 3.8+
**Dependencies**: pandas, pdfplumber, openpyxl
