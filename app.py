import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
from contract_processor import ContractProcessingAgent
from utils.helpers import get_logger

logger = get_logger(__name__)

def init_session_state():
    """Initialize session state variables"""
    if 'openai_api_key' not in st.session_state:
        st.session_state.openai_api_key = None
    if 'processor' not in st.session_state:
        st.session_state.processor = None

def create_visualizations(result):
    """Create visualizations for contract analysis"""
    st.header("📊 Analysis Visualizations")

    # 1. Clause Categories Distribution
    with st.container():
        st.subheader("Distribution of Clause Categories")
        categories = [clause.clause_category for clause in result.document.clauses]
        category_counts = pd.Series(categories).value_counts()

        fig1 = go.Figure(data=[go.Pie(
            labels=category_counts.index,
            values=category_counts.values,
            hole=.3  # Makes it a donut chart
        )])
        fig1.update_layout(
            title="Clause Categories Distribution",
            height=400
        )
        st.plotly_chart(fig1, use_container_width=True)

    # 2. Confidence Scores Chart
    with st.container():
        st.subheader("Analysis Confidence by Clause")
        confidence_scores = [clause.metadata.confidence_score for clause in result.document.clauses]
        clause_names = [clause.clause_name for clause in result.document.clauses]

        fig2 = go.Figure(data=[go.Bar(
            x=clause_names,
            y=confidence_scores,
            marker_color='lightblue'
        )])
        fig2.update_layout(
            title="Clause Analysis Confidence Scores",
            xaxis_title="Clause Name",
            yaxis_title="Confidence Score",
            height=400,
            xaxis_tickangle=-45
        )
        st.plotly_chart(fig2, use_container_width=True)

    # 3. Timeline of Key Dates
    all_dates = []
    date_labels = []
    for clause in result.document.clauses:
        if clause.related_dates:
            for date in clause.related_dates:
                all_dates.append(date)
                date_labels.append(clause.clause_name)

    if all_dates:  # Only show if we have dates
        with st.container():
            st.subheader("Contract Timeline")
            fig3 = go.Figure(data=[go.Scatter(
                x=all_dates,
                y=date_labels,
                mode='markers+text',
                marker=dict(size=12),
                text=all_dates,
                textposition="top center"
            )])
            fig3.update_layout(
                title="Key Dates Timeline",
                xaxis_title="Date",
                yaxis_title="Clause",
                height=max(300, len(all_dates) * 50)  # Dynamic height based on number of dates
            )
            st.plotly_chart(fig3, use_container_width=True)

def main():
    st.set_page_config(
        page_title="Contract Analysis Tool",
        page_icon="📄",
        layout="wide"
    )

    init_session_state()

    # Sidebar for API configuration
    with st.sidebar:
        st.header("🔑 API Configuration")
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=st.session_state.openai_api_key if st.session_state.openai_api_key else "",
            help="Enter your OpenAI API key"
        )

        if api_key:
            st.session_state.openai_api_key = api_key
            if not st.session_state.processor:
                try:
                    st.session_state.processor = ContractProcessingAgent(api_key=api_key)
                    st.success("✅ Successfully connected to API")
                except Exception as e:
                    st.error(f"Failed to initialize: {str(e)}")
        else:
            st.warning("Please provide OpenAI API key to continue")

    # Main content
    st.title("📄 Contract Analysis Tool")
    st.markdown("""
    This tool analyzes contract documents by:
    1. Extracting key metadata and clauses
    2. Classifying contract sections
    3. Identifying important entities and dates
    4. Generating an enhanced version with improved clarity
    """)

    # File upload
    if not st.session_state.openai_api_key:
        st.info("👈 Please configure your OpenAI API key in the sidebar to begin")
        return

    uploaded_file = st.file_uploader("Upload Contract (PDF)", type=['pdf'])

    if uploaded_file:
        with st.spinner("Processing contract..."):
            try:
                # Save uploaded file temporarily and process it
                with Path("temp.pdf").open("wb") as f:
                    f.write(uploaded_file.getbuffer())

                result = st.session_state.processor.process_pdf("temp.pdf")

                if result.status == "success":
                    # Display results in expandable sections
                    st.success("✅ Contract processed successfully")

                    with st.expander("📋 Contract Overview", expanded=True):
                        st.write(f"**Title:** {result.document.contract_title}")
                        st.write(f"**Date:** {result.document.contract_date}")

                        st.subheader("Parties Involved")
                        for party in result.document.parties_involved:
                            st.write(f"- {party.party_name} ({party.role})")

                    with st.expander("📝 Contract Clauses"):
                        st.write(f"**Number of Clauses:** {len(result.document.clauses)}")
                        for i, clause in enumerate(result.document.clauses, 1):
                            st.markdown(f"**Clause {i}: {clause.clause_name}**")
                            st.write(f"Category: {clause.clause_category}")
                            st.write(f"Text: {clause.clause_text}")
                            if clause.related_dates:
                                st.write(f"Dates: {', '.join(clause.related_dates)}")
                            if clause.related_amounts:  # Changed from amounts to related_amounts
                                st.write(f"Amounts: {', '.join(clause.related_amounts)}")
                            # Display metadata
                            st.write(f"Confidence Score: {clause.metadata.confidence_score}")
                            st.write(f"Extracted By: {clause.metadata.extracted_by}")
                            if clause.section_name:  # Optional field
                                st.write(f"Section: {clause.section_name}")
                            st.markdown("---")

                    with st.expander("📊 Summary"):
                        st.write(result.document.summary)

                    # Show visualizations
                    create_visualizations(result)

                else:
                    st.error(f"❌ Error processing contract: {result.error}")

            except Exception as e:
                st.error(f"Processing failed: {str(e)}")
                logger.error(f"Processing failed: {str(e)}", exc_info=True)
            finally:
                # Clean up temporary file
                if Path("temp.pdf").exists():
                    Path("temp.pdf").unlink()

if __name__ == "__main__":
    main()