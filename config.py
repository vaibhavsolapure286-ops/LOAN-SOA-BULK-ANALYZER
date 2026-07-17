"""
Configuration module for Loan SOA Bulk Analyzer
"""

import os
from pathlib import Path

# Directory Configuration
BASE_DIR = Path(__file__).resolve().parent
INPUT_PDF_DIR = BASE_DIR / "input_pdfs"
OUTPUT_DIR = BASE_DIR / "output"

# Ensure directories exist
INPUT_PDF_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Output file configuration
OUTPUT_EXCEL_FILE = OUTPUT_DIR / "loan_portfolio_analysis.xlsx"

# EMI Detection Keywords
EMI_KEYWORDS = [
    "NACH Presented",
    "EMI Received",
    "IMPS Received",
    "Amount Received as EMI",
    "EMI paid",
    "Payment Received",
]

# Bounce Detection Keywords
BOUNCE_KEYWORDS = [
    "Bounced Return",
    "Bounce",
    "Bouncing Charges",
    "Return Charges",
    "BOUNCE",
]

# EMI Due Date
EMI_DUE_DATE = 8  # 8th of every month

# Risk Grading Configuration
RISK_GRADES = {
    "A": (0, 0),  # 0 bounces
    "B": (1, 2),  # 1-2 bounces
    "C": (3, 5),  # 3-5 bounces
    "D": (6, float("inf")),  # >5 bounces
}

# Sheet Names for Excel Export
SHEET_NAMES = {
    "portfolio_summary": "Portfolio Summary",
    "bounce_details": "Bounce Details",
    "late_emi_details": "Late EMI Details",
    "individual_loan_summary": "Individual Loan Summary",
}
