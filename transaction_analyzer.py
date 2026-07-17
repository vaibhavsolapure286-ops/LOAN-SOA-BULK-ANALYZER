"""
Transaction Analysis Module for Loan SOA Bulk Analyzer
Analyzes EMI payments, bounces, and late payments.
"""

import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging

from config import (
    EMI_KEYWORDS,
    BOUNCE_KEYWORDS,
    EMI_DUE_DATE,
    RISK_GRADES,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransactionAnalyzer:
    """Analyze transactions for EMI receipts, bounces, and late payments."""

    def __init__(self):
        """Initialize the transaction analyzer."""
        self.bounce_events = []
        self.emi_events = []
        self.late_emi_events = []

    @staticmethod
    def detect_emi_receipt(description: str) -> bool:
        """
        Detect if a transaction is an EMI receipt.

        Args:
            description: Transaction description

        Returns:
            True if EMI receipt detected, False otherwise
        """
        return any(
            keyword.lower() in description.lower() for keyword in EMI_KEYWORDS
        )

    @staticmethod
    def detect_bounce(description: str) -> bool:
        """
        Detect if a transaction is a bounce event.

        Args:
            description: Transaction description

        Returns:
            True if bounce detected, False otherwise
        """
        return any(
            keyword.lower() in description.lower() for keyword in BOUNCE_KEYWORDS
        )

    @staticmethod
    def parse_date(date_str: str) -> Optional[datetime]:
        """
        Parse date string from transaction.

        Args:
            date_str: Date string in various formats

        Returns:
            datetime object or None if parsing fails
        """
        date_formats = [
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%d/%m/%y",
            "%d-%m-%y",
            "%Y-%m-%d",
            "%d/%B/%Y",
            "%d/%b/%Y",
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        logger.warning(f"Could not parse date: {date_str}")
        return None

    @staticmethod
    def get_emi_due_date(payment_date: datetime) -> datetime:
        """
        Get the EMI due date for a given payment month.
        EMI is due on the 8th of the month.

        Args:
            payment_date: The date of payment

        Returns:
            datetime object for the 8th of the payment month
        """
        return payment_date.replace(day=EMI_DUE_DATE)

    @staticmethod
    def is_late_payment(payment_date: datetime, due_date: datetime) -> bool:
        """
        Check if a payment is late.

        Args:
            payment_date: Actual payment date
            due_date: Due date for the payment

        Returns:
            True if payment is late, False otherwise
        """
        return payment_date > due_date

    def analyze_transactions(self, transactions: List[Dict]) -> Dict:
        """
        Analyze a list of transactions for EMI receipts and bounces.

        Args:
            transactions: List of transaction dictionaries

        Returns:
            Dictionary containing analysis results
        """
        bounce_count = 0
        bounce_details = []
        emi_count = 0
        emi_details = []
        late_emi_count = 0
        late_emi_details = []

        for transaction in transactions:
            description = transaction.get("description", "")
            date_str = transaction.get("date", "")
            amount = transaction.get("amount", 0)

            payment_date = self.parse_date(date_str)
            if not payment_date:
                continue

            # Check for bounce
            if self.detect_bounce(description):
                bounce_count += 1
                bounce_details.append(
                    {
                        "date": date_str,
                        "description": description,
                        "amount": amount,
                    }
                )

            # Check for EMI receipt
            if self.detect_emi_receipt(description):
                emi_count += 1
                due_date = self.get_emi_due_date(payment_date)

                if self.is_late_payment(payment_date, due_date):
                    late_emi_count += 1
                    late_emi_details.append(
                        {
                            "date": date_str,
                            "due_date": due_date.strftime("%d-%m-%Y"),
                            "description": description,
                            "amount": amount,
                            "days_late": (
                                payment_date - due_date
                            ).days,
                        }
                    )

                emi_details.append(
                    {
                        "date": date_str,
                        "description": description,
                        "amount": amount,
                        "is_late": self.is_late_payment(payment_date, due_date),
                    }
                )

        return {
            "bounce_count": bounce_count,
            "bounce_details": bounce_details,
            "emi_count": emi_count,
            "emi_details": emi_details,
            "late_emi_count": late_emi_count,
            "late_emi_details": late_emi_details,
        }

    @staticmethod
    def assign_risk_grade(bounce_count: int) -> str:
        """
        Assign risk grade based on bounce count.

        Args:
            bounce_count: Total number of bounces

        Returns:
            Risk grade (A, B, C, or D)
        """
        for grade, (min_bounces, max_bounces) in RISK_GRADES.items():
            if min_bounces <= bounce_count <= max_bounces:
                return grade

        return "D"  # Default to highest risk

    def analyze_loan_portfolio(self, loans_data: List[Dict]) -> List[Dict]:
        """
        Analyze complete loan portfolio.

        Args:
            loans_data: List of loan data dictionaries

        Returns:
            List of analyzed loan dictionaries with risk grades
        """
        analyzed_loans = []

        for loan in loans_data:
            if not loan or "transactions" not in loan:
                continue

            transactions = loan.get("transactions", [])
            analysis = self.analyze_transactions(transactions)

            bounce_count = analysis["bounce_count"]
            risk_grade = self.assign_risk_grade(bounce_count)

            analyzed_loan = {
                "customer_name": loan.get("customer_name"),
                "loan_number": loan.get("loan_number"),
                "loan_amount": loan.get("loan_amount"),
                "emi_amount": loan.get("emi_amount"),
                "current_pos": loan.get("current_pos"),
                "total_bounces": bounce_count,
                "late_emi_count": analysis["late_emi_count"],
                "risk_grade": risk_grade,
                "emi_count": analysis["emi_count"],
                "bounce_details": analysis["bounce_details"],
                "late_emi_details": analysis["late_emi_details"],
                "pdf_name": loan.get("pdf_name"),
            }

            analyzed_loans.append(analyzed_loan)

        return analyzed_loans
