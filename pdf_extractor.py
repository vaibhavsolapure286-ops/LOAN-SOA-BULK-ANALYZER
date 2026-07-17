"""
PDF Extraction Module for Loan SOA Bulk Analyzer
Extracts text and structured data from PDF files.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pdfplumber
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extract text and structured data from PDF files."""

    def __init__(self):
        """Initialize the PDF extractor."""
        self.loan_data = []

    @staticmethod
    def extract_text_from_pdf(pdf_path: Path) -> str:
        """
        Extract all text from a PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Concatenated text from all pages
        """
        try:
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
            return text
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            return ""

    @staticmethod
    def extract_customer_name(text: str) -> Optional[str]:
        """
        Extract customer name from SOA text.

        Args:
            text: Extracted PDF text

        Returns:
            Customer name or None
        """
        # Common patterns for customer name
        patterns = [
            r"Customer\s*Name\s*[:=]\s*([A-Za-z\s\.]+)",
            r"Applicant\s*Name\s*[:=]\s*([A-Za-z\s\.]+)",
            r"Account\s*Holder\s*[:=]\s*([A-Za-z\s\.]+)",
            r"^([A-Z][A-Za-z\s\.]+)(?=\n.*Loan|Application)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()

        return None

    @staticmethod
    def extract_loan_number(text: str) -> Optional[str]:
        """
        Extract loan number from SOA text.

        Args:
            text: Extracted PDF text

        Returns:
            Loan number or None
        """
        patterns = [
            r"Loan\s*(?:Number|ID|No\.?)\s*[:=]\s*([A-Za-z0-9\-/]+)",
            r"Loan\s*Account\s*[:=]\s*([A-Za-z0-9\-/]+)",
            r"Account\s*Number\s*[:=]\s*([A-Za-z0-9\-/]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    @staticmethod
    def extract_loan_amount(text: str) -> Optional[float]:
        """
        Extract original loan amount from SOA text.

        Args:
            text: Extracted PDF text

        Returns:
            Loan amount or None
        """
        patterns = [
            r"Loan\s*Amount\s*[:=]\s*(?:Rs\.?|₹)?\s*([\d,]+\.?\d*)",
            r"Principal\s*Amount\s*[:=]\s*(?:Rs\.?|₹)?\s*([\d,]+\.?\d*)",
            r"Sanctioned\s*Amount\s*[:=]\s*(?:Rs\.?|₹)?\s*([\d,]+\.?\d*)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(",", "")
                try:
                    return float(amount_str)
                except ValueError:
                    continue

        return None

    @staticmethod
    def extract_emi_amount(text: str) -> Optional[float]:
        """
        Extract EMI amount from SOA text.

        Args:
            text: Extracted PDF text

        Returns:
            EMI amount or None
        """
        patterns = [
            r"EMI\s*Amount\s*[:=]\s*(?:Rs\.?|₹)?\s*([\d,]+\.?\d*)",
            r"Monthly\s*Installment\s*[:=]\s*(?:Rs\.?|₹)?\s*([\d,]+\.?\d*)",
            r"Installment\s*Amount\s*[:=]\s*(?:Rs\.?|₹)?\s*([\d,]+\.?\d*)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(",", "")
                try:
                    return float(amount_str)
                except ValueError:
                    continue

        return None

    @staticmethod
    def extract_current_pos(text: str) -> Optional[float]:
        """
        Extract current POS (Principal Outstanding) from SOA text.
        Uses the last balance appearing in the ledger.

        Args:
            text: Extracted PDF text

        Returns:
            Current POS or None
        """
        patterns = [
            r"Outstanding\s*Balance\s*[:=]\s*(?:Rs\.?|₹)?\s*([\d,]+\.?\d*)",
            r"Principal\s*Outstanding\s*[:=]\s*(?:Rs\.?|₹)?\s*([\d,]+\.?\d*)",
            r"Balance\s*Amount\s*[:=]\s*(?:Rs\.?|₹)?\s*([\d,]+\.?\d*)",
            r"Remaining\s*Balance\s*[:=]\s*(?:Rs\.?|₹)?\s*([\d,]+\.?\d*)",
        ]

        # Find all matches and return the last one (most recent)
        all_matches = []
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                amount_str = match.group(1).replace(",", "")
                try:
                    all_matches.append(float(amount_str))
                except ValueError:
                    continue

        return all_matches[-1] if all_matches else None

    @staticmethod
    def extract_transactions(text: str) -> List[Dict]:
        """
        Extract transaction details from SOA text.

        Args:
            text: Extracted PDF text

        Returns:
            List of transaction dictionaries
        """
        transactions = []
        # Pattern to match transaction lines
        # Adjust based on your SOA format
        pattern = r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\s+(.+?)\s+(?:Rs\.?|₹)?\s*([\d,]+\.?\d*)"

        matches = re.finditer(pattern, text)
        for match in matches:
            try:
                date, description, amount = match.groups()
                amount = float(amount.replace(",", ""))
                transactions.append(
                    {
                        "date": date,
                        "description": description.strip(),
                        "amount": amount,
                    }
                )
            except (ValueError, IndexError):
                continue

        return transactions

    def process_pdf(self, pdf_path: Path) -> Dict:
        """
        Process a single PDF and extract all relevant information.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dictionary containing extracted loan information
        """
        logger.info(f"Processing PDF: {pdf_path.name}")

        text = self.extract_text_from_pdf(pdf_path)

        if not text:
            logger.warning(f"No text extracted from {pdf_path.name}")
            return {}

        loan_info = {
            "pdf_name": pdf_path.name,
            "customer_name": self.extract_customer_name(text),
            "loan_number": self.extract_loan_number(text),
            "loan_amount": self.extract_loan_amount(text),
            "emi_amount": self.extract_emi_amount(text),
            "current_pos": self.extract_current_pos(text),
            "transactions": self.extract_transactions(text),
            "raw_text": text,
        }

        return loan_info

    def process_all_pdfs(self, pdf_directory: Path) -> List[Dict]:
        """
        Process all PDF files in a directory.

        Args:
            pdf_directory: Path to directory containing PDF files

        Returns:
            List of extracted loan information dictionaries
        """
        pdf_files = list(pdf_directory.glob("*.pdf"))

        if not pdf_files:
            logger.warning(f"No PDF files found in {pdf_directory}")
            return []

        logger.info(f"Found {len(pdf_files)} PDF files to process")

        self.loan_data = [self.process_pdf(pdf) for pdf in pdf_files]

        return self.loan_data
