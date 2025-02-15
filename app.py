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


def create_clause_category_chart(result):
    """Create an enhanced donut chart for clause categories"""
    categories = [clause.clause_category for clause in result.document.clauses]
    category_counts = pd.Series(categories).value_counts()

    colors = ['#FF9999', '#66B2FF', '#99FF99', '#FFCC99', '#FF99CC', '#99CCFF']
    fig = go.Figure(data=[go.Pie(
        labels=category_counts.index,
        values=category_counts.values,
        hole=0.4,
        marker=dict(colors=colors),
        textinfo='label+percent',
        textposition='outside',
        pull=[0.1] * len(category_counts)
    )])

    fig.update_layout(
        title={
            'text': "Distribution of Clause Categories",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 24}
        },
        showlegend=False,
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig


def create_confidence_chart(result):
    """Create an enhanced bar chart for confidence scores"""
    confidence_scores = [clause.metadata.confidence_score for clause in result.document.clauses]
    clause_names = [clause.clause_name for clause in result.document.clauses]

    fig = go.Figure(data=[go.Bar(
        x=clause_names,
        y=confidence_scores,
        marker_color='#66B2FF',
        marker_line_color='#3399FF',
        marker_line_width=1.5,
        opacity=0.8
    )])

    fig.update_layout(
        title={
            'text': "Clause Analysis Confidence Scores",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 24}
        },
        xaxis_title="Clause Name",
        yaxis_title="Confidence Score",
        height=400,
        xaxis_tickangle=-45,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig


def create_timeline_chart(result):
    """Create an enhanced timeline visualization"""
    all_dates = []
    date_labels = []
    for clause in result.document.clauses:
        if clause.related_dates:
            for date in clause.related_dates:
                all_dates.append(date)
                date_labels.append(clause.clause_name)

    if not all_dates:
        return None

    fig = go.Figure(data=[go.Scatter(
        x=all_dates,
        y=date_labels,
        mode='markers+text',
        marker=dict(
            size=15,
            color='#66B2FF',
            symbol='diamond',
            line=dict(color='#3399FF', width=2)
        ),
        text=all_dates,
        textposition="top center",
        textfont=dict(size=12)
    )])

    fig.update_layout(
        title={
            'text': "Contract Timeline",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 24}
        },
        xaxis_title="Date",
        yaxis_title="Clause",
        height=max(300, len(all_dates) * 50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    return fig


def display_contract_overview(result):
    """Display enhanced contract overview section"""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📋 Contract Details")
        st.markdown(f"**Title:** {result.document.contract_title}")
        st.markdown(f"**Date:** {result.document.contract_date}")

    with col2:
        st.markdown("### 👥 Parties Involved")
        for party in result.document.parties_involved:
            st.markdown(f"- **{party.party_name}** ({party.role})")


def display_clauses(result):
    """Display enhanced clauses section"""
    st.markdown("## 📝 Contract Clauses Analysis")
    st.markdown(f"**Total Clauses:** {len(result.document.clauses)}")

    for i, clause in enumerate(result.document.clauses, 1):
        with st.expander(f"Clause {i}: {clause.clause_name}"):
            cols = st.columns([2, 1])

            with cols[0]:
                st.markdown("#### Main Content")
                st.markdown(f"**Category:** {clause.clause_category}")
                st.markdown("**Text:**")
                st.markdown(f">{clause.clause_text}")

            with cols[1]:
                st.markdown("#### Additional Information")
                if clause.related_dates:
                    st.markdown("**Key Dates:**")
                    for date in clause.related_dates:
                        st.markdown(f"- {date}")

                if clause.related_amounts:
                    st.markdown("**Related Amounts:**")
                    for amount in clause.related_amounts:
                        st.markdown(f"- {amount}")

                st.progress(clause.metadata.confidence_score,
                            text=f"Confidence Score: {clause.metadata.confidence_score:.0%}")


def main():
    st.set_page_config(
        page_title="Smart Contract Analyzer",
        page_icon="📑",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom styling
    st.markdown("""
        <style>
        .main .block-container { padding-top: 2rem; }
        </style>
    """, unsafe_allow_html=True)

    init_session_state()

    # Sidebar configuration
    with st.sidebar:
        st.image("contract_img.png", width=150)
        st.markdown("## ⚙️ Configuration")

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
                    st.success("✅ API Connected Successfully")
                except Exception as e:
                    st.error(f"❌ Connection Failed: {str(e)}")
        else:
            st.warning("🔑 API Key Required")

    # Main content
    st.markdown("# 📑 Smart Contract Analyzer")
    st.markdown("""
    Transform your contract analysis workflow with AI-powered insights:
    - 🔍 **Intelligent Extraction** of key metadata and clauses
    - 🏷️ **Smart Classification** of contract sections
    - 📅 **Automated Detection** of important dates and entities
    - 📊 **Visual Analytics** for better understanding
    """)

    if not st.session_state.openai_api_key:
        st.info("👈 Please provide your OpenAI API key in the sidebar to begin")
        return

    uploaded_file = st.file_uploader("📤 Upload Contract Document", type=['pdf'])

    if uploaded_file:
        with st.spinner("🔄 Processing your contract..."):
            try:
                with Path("temp.pdf").open("wb") as f:
                    f.write(uploaded_file.getbuffer())

                result = st.session_state.processor.process_pdf("temp.pdf")

                if result.status == "success":
                    st.success("✅ Analysis Complete!")

                    # Display contract overview
                    display_contract_overview(result)

                    # Create three columns for metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Clauses", len(result.document.clauses))
                    with col2:
                        avg_confidence = sum(c.metadata.confidence_score for c in result.document.clauses) / len(
                            result.document.clauses)
                        st.metric("Average Confidence", f"{avg_confidence:.1%}")
                    with col3:
                        st.metric("Parties Involved", len(result.document.parties_involved))

                    # Display clauses
                    display_clauses(result)

                    # Visualizations section
                    st.markdown("## 📊 Visual Analytics")

                    tab1, tab2, tab3 = st.tabs(["Categories", "Confidence Scores", "Timeline"])

                    with tab1:
                        st.plotly_chart(create_clause_category_chart(result), use_container_width=True)
                    with tab2:
                        st.plotly_chart(create_confidence_chart(result), use_container_width=True)
                    with tab3:
                        timeline_chart = create_timeline_chart(result)
                        if timeline_chart:
                            st.plotly_chart(timeline_chart, use_container_width=True)
                        else:
                            st.info("No timeline data available")

                    # Summary section
                    st.markdown("## 📋 Executive Summary")
                    st.markdown(result.document.summary)

                else:
                    st.error(f"❌ Processing Error: {result.error}")

            except Exception as e:
                st.error(f"❌ Analysis Failed: {str(e)}")
                logger.error(f"Analysis failed: {str(e)}", exc_info=True)
            finally:
                if Path("temp.pdf").exists():
                    Path("temp.pdf").unlink()


if __name__ == "__main__":
    main()