import streamlit as st
from pathlib import Path
from agents.contract_processor import ContractProcessingAgent
from components.charts.category_chart import create_clause_category_chart
from components.charts.confidence_chart import create_confidence_chart
from components.charts.timeline_chart import create_timeline_chart
from components.displays.contract_overview import display_contract_overview
from components.displays.clause_display import display_clauses
from utils.helpers import get_logger

logger = get_logger(__name__)

def init_session_state():
    """Initialize session state variables"""
    if 'openai_api_key' not in st.session_state:
        st.session_state.openai_api_key = None
    if 'deepseek_api_key' not in st.session_state:  # Add this
        st.session_state.deepseek_api_key = None
    if 'processor' not in st.session_state:
        st.session_state.processor = None

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

        openai_api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=st.session_state.openai_api_key if st.session_state.openai_api_key else "",
            help="Enter your OpenAI API key"
        )

        deepseek_api_key = st.text_input(  # Add this
            "DeepSeek API Key",
            type="password",
            value=st.session_state.deepseek_api_key if st.session_state.deepseek_api_key else "",
            help="Enter your DeepSeek API key"
        )

        if openai_api_key and deepseek_api_key:
            st.session_state.openai_api_key = openai_api_key
            st.session_state.deepseek_api_key = deepseek_api_key
            if not st.session_state.processor:
                try:
                    st.session_state.processor = ContractProcessingAgent(
                        openai_api_key=openai_api_key,
                        deepseek_api_key=deepseek_api_key
                    )
                    st.success("✅ APIs Connected Successfully")
                except Exception as e:
                    st.error(f"❌ Connection Failed: {str(e)}")
        else:
            st.warning("🔑 API Keys Required")

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