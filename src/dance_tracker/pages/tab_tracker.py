import streamlit as st
import pandas as pd

from dance_tracker.constants import (
    ALL_DANCES,
    DANCE_STYLES,
    DANCES_BY_STYLE,
    INSTRUCTORS,
    LESSON_TYPES,
    MONTHS_ORDER,
    PRIORITIES,
)
from dance_tracker.data_io import (
    add_entry,
    filter_data,
    load_from_upload,
    save_data,
    to_excel_bytes,
)


def _summary_metrics(df: pd.DataFrame):
    st.subheader("Summary")
    total = len(df)
    coaching = len(df[df["Lesson Type"] == "Coaching Lesson"])
    dance_types = df["Dance Type"].apply(
        lambda v: [x.strip() for x in str(v).replace("\n", ",").split(",") if x.strip()]
    ).explode().dropna()
    unique_dances = dance_types[dance_types != ""].nunique()
    instructors = df["Instructor(s)"].apply(
        lambda v: [x.strip() for x in str(v).replace("+", ",").split(",") if x.strip()]
    ).explode().dropna()
    unique_instructors = instructors[instructors != ""].nunique()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Lessons", total)
    c2.metric("Coaching Lessons", coaching)
    c3.metric("Dance Types", unique_dances)
    c4.metric("Unique Instructors", unique_instructors)

    st.markdown("---")
    st.markdown("**Lessons by Year & Month**")
    year_month = (
        df[df["Year"].astype(str).str.strip().ne("")]
        .groupby(["Year", "Month"])
        .size()
        .reset_index(name="Count")
    )
    if not year_month.empty:
        year_month["Month"] = pd.Categorical(
            year_month["Month"].str.strip(), categories=MONTHS_ORDER, ordered=True
        )
        year_month = year_month.sort_values(["Year", "Month"])
        pivot = year_month.pivot(index="Year", columns="Month", values="Count")
        pivot = pivot.reindex(columns=MONTHS_ORDER, fill_value=0).fillna(0).astype(int)
        st.dataframe(pivot, use_container_width=True)


def _add_entry_form(df: pd.DataFrame) -> pd.DataFrame:
    with st.expander("Add New Lesson", expanded=False):
        with st.form("add_lesson_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                date = st.date_input("Date")
                dance_style = st.selectbox("Dance Style", [""] + DANCE_STYLES)
                dance_type_options = DANCES_BY_STYLE.get(dance_style, ALL_DANCES) if dance_style else ALL_DANCES
                dance_type = st.selectbox("Dance Type", [""] + dance_type_options)
                lesson_type = st.selectbox("Lesson Type", LESSON_TYPES)
            with col2:
                instructor = st.selectbox("Instructor", [""] + INSTRUCTORS)
                priority = st.selectbox("Priority", ["", "High", "Low"])
                notes = st.text_area("Notes (optional)")
                reference = st.text_input("Reference (optional)")

            submitted = st.form_submit_button("Save Lesson")
            if submitted:
                if not str(date):
                    st.error("Date is required.")
                else:
                    parsed = pd.to_datetime(str(date))
                    entry = {
                        "Year": parsed.year,
                        "Month": parsed.strftime("%b"),
                        "Day": parsed.strftime("%a"),
                        "Date": parsed.strftime("%-d-%b-%y") if hasattr(parsed, "strftime") else str(date),
                        "Instructor(s)": instructor,
                        "Priority": priority,
                        "Lesson Type": lesson_type,
                        "Dance Type": dance_type,
                        "Note + Homework": notes,
                        "Reference": reference,
                    }
                    try:
                        entry["Date"] = parsed.strftime("%d-%b-%y").lstrip("0")
                    except Exception:
                        entry["Date"] = str(date)
                    df = add_entry(df, entry)
                    save_data(df)
                    st.success("Lesson saved!")
                    st.session_state["df"] = df
    return df


def _lesson_log(df: pd.DataFrame):
    st.subheader("Lesson Log")
    display_cols = ["Year", "Month", "Day", "Date", "Dance Style", "Dance Type",
                    "Lesson Type", "Instructor(s)", "Priority", "Note + Homework", "Reference"]
    show_cols = [c for c in display_cols if c in df.columns]
    st.dataframe(
        df[show_cols].replace("", "—"),
        use_container_width=True,
        height=500,
    )


def render(df: pd.DataFrame) -> pd.DataFrame:
    st.title("Dance Lesson Tracker")

    # Upload section
    col_up, col_dl = st.columns([3, 1])
    with col_up:
        uploaded = st.file_uploader(
            "Upload a new Practice Log (CSV or Excel)",
            type=["csv", "xlsx", "xls"],
            key="uploader",
        )
        if uploaded:
            df = load_from_upload(uploaded)
            save_data(df)
            st.session_state["df"] = df
            st.success("File uploaded and saved! App refreshed with new data.")
            st.rerun()

    with col_dl:
        st.markdown("<br>", unsafe_allow_html=True)
        excel_bytes = to_excel_bytes(df)
        st.download_button(
            label="Download as Excel",
            data=excel_bytes,
            file_name="practice_log_export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    st.markdown("---")

    # Sidebar filters
    with st.sidebar:
        st.header("Filters & Search")

        keyword = st.text_input("Search by keyword", key="kw_search")

        years_available = sorted(
            [str(y) for y in df["Year"].unique() if str(y).strip() not in ("", "0")]
        )
        selected_years = st.multiselect("Year", years_available, default=years_available)

        months_available = [m for m in MONTHS_ORDER if m in df["Month"].str.strip().unique()]
        selected_months = st.multiselect("Month", months_available, default=months_available)

        selected_instructors = st.multiselect("Instructor", INSTRUCTORS)
        selected_priorities = st.multiselect("Priority", ["High", "Low", "(blank)"])
        selected_lesson_types = st.multiselect("Lesson Type", LESSON_TYPES)

        selected_styles = st.multiselect("Dance Style", DANCE_STYLES)
        if selected_styles:
            dance_type_options = [d for s in selected_styles for d in DANCES_BY_STYLE.get(s, [])]
        else:
            dance_type_options = ALL_DANCES
        selected_dances = st.multiselect("Dance Type", dance_type_options)

    # Map "(blank)" back to ""
    priorities_filter = []
    for p in selected_priorities:
        priorities_filter.append("" if p == "(blank)" else p)

    filtered = filter_data(
        df,
        years=selected_years if selected_years else None,
        months=selected_months if selected_months else None,
        instructors=selected_instructors if selected_instructors else None,
        priorities=priorities_filter if selected_priorities else None,
        lesson_types=selected_lesson_types if selected_lesson_types else None,
        dance_styles=selected_styles if selected_styles else None,
        dance_types=selected_dances if selected_dances else None,
        keyword=keyword,
    )

    _summary_metrics(filtered)

    df = _add_entry_form(df)

    _lesson_log(filtered)

    return df
