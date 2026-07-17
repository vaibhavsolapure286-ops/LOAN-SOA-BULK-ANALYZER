"""
Main entry point for Loan SOA Bulk Analyzer
Orchestrates PDF extraction, analysis, and Excel export.
"""

import logging
from pathlib import Path

from config import INPUT_PDF_DIR, OUTPUT_EXCEL_FILE
from pdf_extractor import PDFExtractor
from transaction_analyzer import TransactionAnalyzer
from excel_exporter import ExcelExporter

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class LoanSOABulkAnalyzer:
    """Main analyzer orchestrator."""

    def __init__(self):
        """Initialize the analyzer with component modules."""
        self.pdf_extractor = PDFExtractor()
        self.transaction_analyzer = TransactionAnalyzer()
        self.excel_exporter = ExcelExporter(OUTPUT_EXCEL_FILE)

    def run(self, pdf_directory: Path = INPUT_PDF_DIR) -> bool:
        """
        Run the complete analysis pipeline.

        Args:
            pdf_directory: Directory containing PDF files

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("=" * 60)
            logger.info("Starting Loan SOA Bulk Analyzer")
            logger.info("=" * 60)

            # Step 1: Extract data from PDFs
            logger.info(f"Step 1: Extracting data from PDFs in {pdf_directory}")
            loans_data = self.pdf_extractor.process_all_pdfs(pdf_directory)

            if not loans_data:
                logger.error("No loan data extracted from PDFs")
                return False

            logger.info(f"Successfully extracted data from {len(loans_data)} PDF(s)")

            # Step 2: Analyze transactions
            logger.info("Step 2: Analyzing transactions for bounces and late EMIs")
            analyzed_loans = (
                self.transaction_analyzer.analyze_loan_portfolio(loans_data)
            )

            if not analyzed_loans:
                logger.error("No loans were analyzed")
                return False

            logger.info(f"Successfully analyzed {len(analyzed_loans)} loan(s)")

            # Step 3: Export to Excel
            logger.info("Step 3: Exporting analysis to Excel")
            success = self.excel_exporter.export_to_excel(analyzed_loans)

            if not success:
                return False

            # Print summary
            self._print_summary(analyzed_loans)

            logger.info("=" * 60)
            logger.info("Analysis completed successfully!")
            logger.info("=" * 60)

            return True

        except Exception as e:
            logger.error(f"Error during analysis: {e}", exc_info=True)
            return False

    @staticmethod
    def _print_summary(analyzed_loans):
        """
        Print analysis summary to console.

        Args:
            analyzed_loans: List of analyzed loan dictionaries
        """
        logger.info("=" * 60)
        logger.info("ANALYSIS SUMMARY")
        logger.info("=" * 60)

        total_loans = len(analyzed_loans)
        total_bounces = sum(loan["total_bounces"] for loan in analyzed_loans)
        total_late_emis = sum(
            loan["late_emi_count"] for loan in analyzed_loans
        )
        total_loan_amount = sum(
            loan["loan_amount"] or 0 for loan in analyzed_loans
        )
        total_current_pos = sum(
            loan["current_pos"] or 0 for loan in analyzed_loans
        )

        # Risk grade distribution
        risk_grades = {}
        for loan in analyzed_loans:
            grade = loan["risk_grade"]
            risk_grades[grade] = risk_grades.get(grade, 0) + 1

        logger.info(f"Total Loans Analyzed: {total_loans}")
        logger.info(f"Total Loan Amount: Rs. {total_loan_amount:,.2f}")
        logger.info(f"Total Current POS: Rs. {total_current_pos:,.2f}")
        logger.info(f"Total Bounces: {total_bounces}")
        logger.info(f"Total Late EMIs: {total_late_emis}")
        logger.info("\nRisk Grade Distribution:")
        for grade in sorted(risk_grades.keys()):
            logger.info(f"  Grade {grade}: {risk_grades[grade]} loan(s)")

        logger.info("=" * 60)


def main():
    """Main entry point."""
    analyzer = LoanSOABulkAnalyzer()
    success = analyzer.run()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
