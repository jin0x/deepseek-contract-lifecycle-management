import streamlit as st

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