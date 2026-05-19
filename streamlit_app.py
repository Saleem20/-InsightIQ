try:
    from app import *  # noqa: F401,F403
except Exception as exc:
    import traceback

    import streamlit as st

    st.error("InsightIQ could not start.")
    st.write("Please check that app.py and requirements.txt are both uploaded to GitHub.")
    with st.expander("Technical details"):
        st.code("".join(traceback.format_exception(exc)), language="text")
