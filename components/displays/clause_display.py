import streamlit as st

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
