"""
Streamlit Web Interface for Loan SOA Bulk Analyzer
Provides interactive UI for PDF upload and analysis
"""

import streamlit as st
import pandas as pd
import io
from pathlib import Path
import tempfile
import logging
from datetime import datetime

from pdf_extractor import PDFExtractor
from transaction_analyzer import TransactionAnalyzer
from excel_exporter import ExcelExporter

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Loan SOA Bulk Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
    <style>
    .main {
        padding: 0rem 0rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def initialize_session_state():
    """Initialize session state variables."""
    if "analyzed_loans" not in st.session_state:
        st.session_state.analyzed_loans = None
    if "loans_data" not in st.session_state:
        st.session_state.loans_data = None
    if "analysis_complete" not in st.session_state:
        st.session_state.analysis_complete = False

def display_header():
    """Display application header."""
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("# 📊 Loan SOA Bulk Analyzer")
        st.markdown("*Automated PDF extraction and analysis for loan portfolios*")
    with col2:
        st.markdown("")
        st.markdown("")
        if st.button("🔄 Reset", help="Reset all data and start over"):
            st.session_state.analyzed_loans = None
            st.session_state.loans_data = None
            st.session_state.analysis_complete = False
            st.rerun()
    st.markdown("---")

def display_upload_section():
    """Display PDF upload section."""
    st.subheader("📁 Step 1: Upload PDF Files")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        uploaded_files = st.file_uploader(
            "Upload SOA PDF files",
            type="pdf",
            accept_multiple_files=True,
            help="Upload one or multiple SOA PDF files for analysis"
        )
    
    with col2:
        st.metric("Files Uploaded", len(uploaded_files) if uploaded_files else 0)
    
    return uploaded_files

def process_pdfs(uploaded_files):
    """Process uploaded PDF files - NO FILE PATH ISSUES."""
    if not uploaded_files:
        st.warning("⚠️ Please upload at least one PDF file to proceed.")
        return None
    
    st.subheader("⚙️ Step 2: Processing PDFs")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    pdf_extractor = PDFExtractor()
    loans_data = []
    
    for idx, uploaded_file in enumerate(uploaded_files):
        # Update progress
        progress = (idx + 1) / len(uploaded_files)
        progress_bar.progress(progress)
        status_text.text(f"Processing: {uploaded_file.name} ({idx + 1}/{len(uploaded_files)})")
        
        try:
            # Create temporary file with proper cleanup
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getbuffer())
                tmp_path = Path(tmp_file.name)
            
            # Extract data from temporary file
            loan_info = pdf_extractor.process_pdf(tmp_path)
            if loan_info:
                loans_data.append(loan_info)
            
            # Clean up temporary file
            try:
                tmp_path.unlink()
            except Exception as e:
                logger.warning(f"Could not delete temp file: {e}")
            
        except Exception as e:
            st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
            logger.error(f"Error processing {uploaded_file.name}: {e}")
    
    status_text.text("✅ Processing complete!")
    progress_bar.empty()
    
    return loans_data if loans_data else None

def analyze_loans(loans_data):
    """Analyze loan data."""
    if not loans_data:
        st.error("❌ No loan data to analyze.")
        return None
    
    st.subheader("📈 Step 3: Analyzing Loans")
    
    with st.spinner("Analyzing transactions..."):
        transaction_analyzer = TransactionAnalyzer()
        analyzed_loans = transaction_analyzer.analyze_loan_portfolio(loans_data)
    
    st.success("✅ Analysis complete!")
    return analyzed_loans if analyzed_loans else None

def display_summary_metrics(analyzed_loans):
    """Display summary metrics."""
    st.subheader("📊 Portfolio Summary")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Loans",
            len(analyzed_loans),
            "loans analyzed"
        )
    
    with col2:
        total_amount = sum(loan["loan_amount"] or 0 for loan in analyzed_loans)
        st.metric(
            "Total Loan Amount",
            f"₹{total_amount:,.0f}",
            "portfolio value"
        )
    
    with col3:
        total_pos = sum(loan["current_pos"] or 0 for loan in analyzed_loans)
        st.metric(
            "Total POS",
            f"₹{total_pos:,.0f}",
            "outstanding"
        )
    
    with col4:
        total_bounces = sum(loan["total_bounces"] for loan in analyzed_loans)
        st.metric(
            "Total Bounces",
            total_bounces,
            "bounce events"
        )
    
    with col5:
        total_late = sum(loan["late_emi_count"] for loan in analyzed_loans)
        st.metric(
            "Late EMIs",
            total_late,
            "late payments"
        )

def display_risk_distribution(analyzed_loans):
    """Display risk grade distribution."""
    st.subheader("📈 Risk Grade Distribution")
    
    risk_grades = {}
    for loan in analyzed_loans:
        grade = loan["risk_grade"]
        risk_grades[grade] = risk_grades.get(grade, 0) + 1
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Bar chart
        risk_df = pd.DataFrame({
            "Risk Grade": sorted(risk_grades.keys()),
            "Count": [risk_grades[g] for g in sorted(risk_grades.keys())]
        })
        st.bar_chart(risk_df.set_index("Risk Grade"))
    
    with col2:
        # Summary table
        st.write("**Grade Distribution:**")
        for grade in sorted(risk_grades.keys()):
            col_a, col_b = st.columns([2, 1])
            with col_a:
                st.write(f"Grade {grade}")
            with col_b:
                st.metric("", risk_grades[grade], label_visibility="collapsed")

def display_portfolio_table(analyzed_loans):
    """Display portfolio summary table."""
    st.subheader("📋 Portfolio Summary Table")
    
    portfolio_data = []
    for loan in analyzed_loans:
        portfolio_data.append({
            "Loan Number": loan.get("loan_number", "N/A"),
            "Customer Name": loan.get("customer_name", "N/A"),
            "Loan Amount (Rs.)": f"₹{loan.get('loan_amount', 0):,.0f}" if loan.get('loan_amount') else "N/A",
            "EMI (Rs.)": f"₹{loan.get('emi_amount', 0):,.0f}" if loan.get('emi_amount') else "N/A",
            "Current POS (Rs.)": f"₹{loan.get('current_pos', 0):,.0f}" if loan.get('current_pos') else "N/A",
            "Total Bounces": loan.get("total_bounces", 0),
            "Late EMIs": loan.get("late_emi_count", 0),
            "Risk Grade": loan.get("risk_grade", "N/A")
        })
    
    df = pd.DataFrame(portfolio_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    return portfolio_data

def display_bounce_details(analyzed_loans):
    """Display bounce details."""
    st.subheader("⚠️ Bounce Details")
    
    bounce_data = []
    for loan in analyzed_loans:
        for bounce in loan.get("bounce_details", []):
            bounce_data.append({
                "Loan Number": loan.get("loan_number", "N/A"),
                "Customer Name": loan.get("customer_name", "N/A"),
                "Bounce Date": bounce.get("date", "N/A"),
                "Description": bounce.get("description", "N/A"),
                "Amount (Rs.)": f"₹{bounce.get('amount', 0):,.0f}"
            })
    
    if bounce_data:
        df = pd.DataFrame(bounce_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("✅ No bounce events found!")

def display_late_emi_details(analyzed_loans):
    """Display late EMI details."""
    st.subheader("📅 Late EMI Details")
    
    late_emi_data = []
    for loan in analyzed_loans:
        for late_emi in loan.get("late_emi_details", []):
            late_emi_data.append({
                "Loan Number": loan.get("loan_number", "N/A"),
                "Customer Name": loan.get("customer_name", "N/A"),
                "Payment Date": late_emi.get("date", "N/A"),
                "Due Date": late_emi.get("due_date", "N/A"),
                "Days Late": late_emi.get("days_late", 0),
                "Amount (Rs.)": f"₹{late_emi.get('amount', 0):,.0f}"
            })
    
    if late_emi_data:
        df = pd.DataFrame(late_emi_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("✅ No late EMIs found!")

def export_to_excel(analyzed_loans):
    """Export analysis results to Excel."""
    st.subheader("📥 Step 4: Export Results")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("Download your analysis as an Excel file with multiple sheets.")
    
    with col2:
        if st.button("📊 Generate Excel Report", use_container_width=True):
            try:
                # Create temporary buffer for Excel
                output_buffer = io.BytesIO()
                
                # Create exporter and generate sheets
                exporter = ExcelExporter()
                
                # Create dataframes
                portfolio_df = exporter.create_portfolio_summary(analyzed_loans)
                bounce_df = exporter.create_bounce_details(analyzed_loans)
                late_emi_df = exporter.create_late_emi_details(analyzed_loans)
                individual_df = exporter.create_individual_loan_summary(analyzed_loans)
                
                # Write to buffer
                with pd.ExcelWriter(output_buffer, engine="openpyxl") as writer:
                    portfolio_df.to_excel(writer, sheet_name="Portfolio Summary", index=False)
                    bounce_df.to_excel(writer, sheet_name="Bounce Details", index=False)
                    late_emi_df.to_excel(writer, sheet_name="Late EMI Details", index=False)
                    individual_df.to_excel(writer, sheet_name="Individual Loan Summary", index=False)
                
                output_buffer.seek(0)
                
                # Download button
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"loan_portfolio_analysis_{timestamp}.xlsx"
                
                st.download_button(
                    label="📥 Download Excel File",
                    data=output_buffer.getvalue(),
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                st.success("✅ Excel file generated successfully!")
                
            except Exception as e:
                st.error(f"❌ Error generating Excel file: {str(e)}")
                logger.error(f"Error generating Excel: {e}")

def main():
    """Main Streamlit application - ENTRY POINT."""
    initialize_session_state()
    display_header()
    
    # Sidebar documentation
    st.sidebar.markdown("## 📚 Documentation")
    st.sidebar.markdown(
        """
        ### How to Use:
        1. Upload SOA PDF files
        2. Click 'Process PDFs'
        3. Click 'Analyze Loans'
        4. View results & Export
        
        ### Supported Features:
        - Extract loan information
        - Detect EMI receipts
        - Track bounce events
        - Identify late payments
        - Assign risk grades
        
        ### Risk Grades:
        - **A**: 0 bounces (Low Risk)
        - **B**: 1-2 bounces (Medium Risk)
        - **C**: 3-5 bounces (High Risk)
        - **D**: >5 bounces (Very High Risk)
        """
    )
    
    # Main content
    uploaded_files = display_upload_section()
    
    if uploaded_files:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("▶️ Process PDFs", use_container_width=True, key="process_btn"):
                st.session_state.loans_data = process_pdfs(uploaded_files)
                if st.session_state.loans_data:
                    st.success(f"✅ Extracted data from {len(st.session_state.loans_data)} PDF(s)")
        
        with col2:
            if st.session_state.loans_data and st.button("📊 Analyze Loans", use_container_width=True):
                st.session_state.analyzed_loans = analyze_loans(st.session_state.loans_data)
                if st.session_state.analyzed_loans:
                    st.session_state.analysis_complete = True
        
        with col3:
            st.write("")
    
    # Display results if analysis is complete
    if st.session_state.analysis_complete and st.session_state.analyzed_loans:
        st.markdown("---")
        
        # Display metrics
        display_summary_metrics(st.session_state.analyzed_loans)
        
        st.markdown("---")
        
        # Display charts and tables
        display_risk_distribution(st.session_state.analyzed_loans)
        
        st.markdown("---")
        
        # Display detailed data in tabs
        tab1, tab2, tab3 = st.tabs(["Portfolio Summary", "Bounce Details", "Late EMI Details"])
        
        with tab1:
            display_portfolio_table(st.session_state.analyzed_loans)
        
        with tab2:
            display_bounce_details(st.session_state.analyzed_loans)
        
        with tab3:
            display_late_emi_details(st.session_state.analyzed_loans)
        
        st.markdown("---")
        
        # Export section
        export_to_excel(st.session_state.analyzed_loans)

if __name__ == "__main__":
    main()
