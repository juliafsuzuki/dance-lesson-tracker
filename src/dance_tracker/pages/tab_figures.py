import pandas as pd
import streamlit as st

FIGURES_DATA: dict[str, list[dict]] = {
    "Waltz": [],
    "Tango": [],
    "Foxtrot": [],
    "Viennese Waltz": [],
    "Cha Cha": [],
    "Rumba": [],
    "Swing": [],
    "Bolero": [],
    "Mambo": [],
}

DANCE_ORDER = {
    "Smooth": ["Waltz", "Tango", "Foxtrot", "Viennese Waltz"],
    "Rhythm": ["Cha Cha", "Rumba", "Swing", "Bolero", "Mambo"],
}


def _make_empty_table(dance_style: str, dance_type: str) -> pd.DataFrame:
    return pd.DataFrame(
        [{"Dance Style": dance_style, "Dance Type": dance_type, "Dance Figure": ""}] * 5
    )


def _render_style_section(style: str, dances: list[str]):
    st.markdown(f"### {style}")
    for i, dance in enumerate(dances, start=1):
        label = f"0{i} {dance}"
        with st.expander(label, expanded=False):
            figures = FIGURES_DATA.get(dance, [])
            if figures:
                df = pd.DataFrame(figures)
            else:
                df = _make_empty_table(style, dance)
            edited = st.data_editor(
                df,
                num_rows="dynamic",
                use_container_width=True,
                key=f"figures_{dance}",
                column_config={
                    "Dance Style": st.column_config.TextColumn("Dance Style", disabled=True),
                    "Dance Type": st.column_config.TextColumn("Dance Type", disabled=True),
                    "Dance Figure": st.column_config.TextColumn("Dance Figure"),
                },
            )
            FIGURES_DATA[dance] = edited.to_dict("records")


def render(_df=None):
    st.title("Dance Figures")
    st.caption(
        "Placeholder tables for each dance type. "
        "Add figures directly in the table — rows save within your session."
    )

    for style, dances in DANCE_ORDER.items():
        _render_style_section(style, dances)
        st.markdown("---")
