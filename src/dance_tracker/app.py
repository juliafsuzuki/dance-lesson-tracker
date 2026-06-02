import streamlit as st

from dance_tracker.data_io import load_data
from dance_tracker.pages import tab_analysis, tab_figures, tab_tracker


def main():
    st.set_page_config(
        page_title="Dance Lesson Tracker",
        page_icon="💃",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    if "df" not in st.session_state:
        st.session_state["df"] = load_data()

    tab1, tab2, tab3 = st.tabs([
        "Dance Lesson Tracker",
        "Dance Analysis",
        "Dance Figures",
    ])

    with tab1:
        st.session_state["df"] = tab_tracker.render(st.session_state["df"])

    with tab2:
        tab_analysis.render(st.session_state["df"])

    with tab3:
        tab_figures.render()


if __name__ == "__main__":
    main()
