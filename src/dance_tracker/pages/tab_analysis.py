import pandas as pd
import plotly.express as px
import streamlit as st

from dance_tracker.constants import INSTRUCTORS


def _explode_instructors(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["_instructors"] = df["Instructor(s)"].apply(
        lambda v: [x.strip() for x in str(v).replace("+", ",").split(",") if x.strip()]
    )
    return df.explode("_instructors")


def _explode_dances(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["_dances"] = df["Dance Type"].apply(
        lambda v: [x.strip() for x in str(v).replace("\n", ",").split(",") if x.strip()]
    )
    return df.explode("_dances")


def _high_priority_section(df: pd.DataFrame):
    st.subheader("High Priority — Items to Revisit")
    high = df[df["Priority"] == "High"].copy()
    if high.empty:
        st.info("No High Priority lessons found.")
        return
    show_cols = ["Date", "Dance Style", "Dance Type", "Lesson Type", "Instructor(s)", "Note + Homework", "Reference"]
    show_cols = [c for c in show_cols if c in high.columns]
    st.dataframe(
        high[show_cols].replace("", "—"),
        use_container_width=True,
        height=400,
    )
    st.caption(f"{len(high)} lesson(s) marked High Priority")


def _role(name: str) -> str:
    return "Instructor" if name in INSTRUCTORS else "Coach"


def _instructor_breakdown(df: pd.DataFrame):
    st.subheader("Instructor Breakdown")
    exploded = _explode_instructors(df)
    exploded = exploded[exploded["_instructors"].ne("") & exploded["_instructors"].notna()]

    count_by_instructor = (
        exploded.groupby("_instructors").size().reset_index(name="Lessons").sort_values("Lessons", ascending=False)
    )
    count_by_instructor["Role"] = count_by_instructor["_instructors"].apply(_role)
    count_by_instructor = count_by_instructor.rename(columns={"_instructors": "Name"})
    count_by_instructor = count_by_instructor[["Name", "Role", "Lessons"]]

    col1, col2 = st.columns([1, 2])
    with col1:
        st.dataframe(count_by_instructor, use_container_width=True)
    with col2:
        fig = px.bar(
            count_by_instructor,
            x="Name",
            y="Lessons",
            color="Role",
            labels={"Name": "Name", "Lessons": "Lessons"},
            title="Lessons per Instructor / Coach",
            color_discrete_map={"Instructor": "#7B9E87", "Coach": "#E8A598"},
        )
        fig.update_layout(showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Dances per Instructor / Coach**")
    dance_by_instructor = (
        exploded.groupby("_instructors")["Dance Type"]
        .apply(lambda s: ", ".join(sorted(set(
            part.strip()
            for v in s.dropna()
            for part in str(v).replace("\n", ",").split(",")
            if part.strip()
        ))))
        .reset_index()
        .rename(columns={"_instructors": "Name", "Dance Type": "Dances Covered"})
    )
    dance_by_instructor["Role"] = dance_by_instructor["Name"].apply(_role)
    dance_by_instructor = dance_by_instructor[["Name", "Role", "Dances Covered"]]
    st.dataframe(dance_by_instructor, use_container_width=True)


def _coaching_history(df: pd.DataFrame):
    st.subheader("Coaching Lesson History")
    coaching = df[df["Lesson Type"] == "Coaching Lesson"].copy()
    if coaching.empty:
        st.info("No coaching lessons found.")
        return

    def extract_coaches(instructor_str: str) -> str:
        parts = [x.strip() for x in str(instructor_str).replace("+", ",").split(",") if x.strip()]
        coaches = [p for p in parts if p not in INSTRUCTORS]
        return ", ".join(coaches) if coaches else "—"

    def extract_instructor(instructor_str: str) -> str:
        parts = [x.strip() for x in str(instructor_str).replace("+", ",").split(",") if x.strip()]
        regulars = [p for p in parts if p in INSTRUCTORS]
        return ", ".join(regulars) if regulars else "—"

    coaching["Coach"] = coaching["Instructor(s)"].apply(extract_coaches)
    coaching["Instructor"] = coaching["Instructor(s)"].apply(extract_instructor)

    show_cols = ["Date", "Coach", "Instructor", "Dance Type", "Note + Homework"]
    show_cols = [c for c in show_cols if c in coaching.columns]
    st.dataframe(
        coaching[show_cols].replace("", "—"),
        use_container_width=True,
        height=350,
    )
    st.caption(f"{len(coaching)} coaching lesson(s) total")


def _dance_type_breakdown(df: pd.DataFrame):
    st.subheader("Dance Type Breakdown")
    exploded = _explode_dances(df)
    exploded = exploded[exploded["_dances"].ne("") & exploded["_dances"].notna()]

    count_by_dance = (
        exploded.groupby("_dances").size().reset_index(name="Lessons").sort_values("Lessons", ascending=False)
    )

    col1, col2 = st.columns([1, 2])
    with col1:
        st.dataframe(count_by_dance.rename(columns={"_dances": "Dance Type"}), use_container_width=True)
    with col2:
        fig = px.pie(
            count_by_dance,
            names="_dances",
            values="Lessons",
            title="Lessons by Dance Type",
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        st.plotly_chart(fig, use_container_width=True)


def _lessons_over_time(df: pd.DataFrame):
    st.subheader("Lessons Over Time")
    df2 = df.copy()
    df2["_date"] = pd.to_datetime(df2["Date"], dayfirst=False, errors="coerce")
    df2 = df2.dropna(subset=["_date"])
    if df2.empty:
        st.info("Not enough date data to plot a timeline.")
        return
    df2["YearMonth"] = df2["_date"].dt.to_period("M").astype(str)
    monthly = df2.groupby("YearMonth").size().reset_index(name="Lessons")
    fig = px.bar(
        monthly,
        x="YearMonth",
        y="Lessons",
        title="Lessons per Month",
        color_discrete_sequence=["#7B9E87"],
    )
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)


def _dance_style_breakdown(df: pd.DataFrame):
    st.subheader("Dance Style Breakdown")
    style_counts = df[df["Dance Style"].ne("")]["Dance Style"].value_counts().reset_index()
    style_counts.columns = ["Dance Style", "Lessons"]
    if style_counts.empty:
        st.info("Not enough dance style data.")
        return
    fig = px.bar(
        style_counts,
        x="Dance Style",
        y="Lessons",
        title="Lessons by Dance Style",
        color="Dance Style",
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


def render(df: pd.DataFrame):
    st.title("Dance Analysis")

    if df.empty:
        st.warning("No data loaded yet. Upload a Practice Log on the Tracker tab.")
        return

    _high_priority_section(df)
    st.markdown("---")
    _coaching_history(df)
    st.markdown("---")
    _lessons_over_time(df)
    st.markdown("---")
    _dance_style_breakdown(df)
    st.markdown("---")
    _instructor_breakdown(df)
    st.markdown("---")
    _dance_type_breakdown(df)
