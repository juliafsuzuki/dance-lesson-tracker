import io
import re
from pathlib import Path

import pandas as pd

from dance_tracker.constants import (
    COACHING_KEYWORDS,
    COLUMNS,
    DATA_PATH,
    DANCE_STYLE_MAP,
    MONTHS_ORDER,
)


def _normalize_priority(val: str) -> str:
    if pd.isna(val) or str(val).strip() == "":
        return ""
    v = str(val).strip().lower()
    if v in ("high", "1"):
        return "High"
    if v in ("low", "3"):
        return "Low"
    if v == "2":
        return ""
    return str(val).strip()


def _normalize_lesson_type(val: str) -> str:
    if pd.isna(val) or str(val).strip() == "":
        return "Private Lesson"
    v = str(val).strip().lower()
    if any(kw in v for kw in COACHING_KEYWORDS):
        return "Coaching Lesson"
    return "Private Lesson"


def _infer_style(dance_type: str) -> str:
    if pd.isna(dance_type) or str(dance_type).strip() == "":
        return ""
    parts = re.split(r"[,\n+/&]", str(dance_type))
    styles = set()
    for part in parts:
        p = part.strip()
        if p in DANCE_STYLE_MAP:
            styles.add(DANCE_STYLE_MAP[p])
    if len(styles) == 1:
        return styles.pop()
    if len(styles) > 1:
        return ", ".join(sorted(styles))
    return ""


def _fill_date_parts(df: pd.DataFrame) -> pd.DataFrame:
    """Derive Year/Month/Day from the Date column when they're blank."""
    for idx, row in df.iterrows():
        date_val = str(row.get("Date", "")).strip()
        if not date_val or date_val.lower() == "nan":
            continue
        try:
            parsed = pd.to_datetime(date_val, dayfirst=False, errors="coerce")
            if pd.isna(parsed):
                continue
            if pd.isna(row.get("Year")) or str(row.get("Year")).strip() in ("", "nan"):
                df.at[idx, "Year"] = parsed.year
            if pd.isna(row.get("Month")) or str(row.get("Month")).strip() in ("", "nan"):
                df.at[idx, "Month"] = parsed.strftime("%b")
            if pd.isna(row.get("Day")) or str(row.get("Day")).strip() in ("", "nan"):
                df.at[idx, "Day"] = parsed.strftime("%a")
        except Exception:
            pass
    return df


def _parse_raw(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]

    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df = _fill_date_parts(df)

    df["Priority"] = df["Priority"].apply(_normalize_priority)
    df["Lesson Type"] = df["Lesson Type"].apply(_normalize_lesson_type)
    df["Dance Style"] = df["Dance Type"].apply(_infer_style)

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").fillna(0).astype(int)
    df["Year"] = df["Year"].replace(0, "")

    df["Month"] = df["Month"].astype(str).str.strip()
    df["Day"] = df["Day"].astype(str).str.strip()

    df["Date"] = df["Date"].astype(str).str.strip()
    df["Instructor(s)"] = df["Instructor(s)"].astype(str).str.strip()
    df["Dance Type"] = df["Dance Type"].astype(str).str.strip()
    df["Note + Homework"] = df["Note + Homework"].astype(str).str.strip()
    df["Reference"] = df["Reference"].astype(str).str.strip()

    df = df.replace("nan", "")

    df["_sort_date"] = pd.to_datetime(df["Date"], dayfirst=False, errors="coerce")
    df = df.sort_values("_sort_date", ascending=False).drop(columns=["_sort_date"])
    df = df.reset_index(drop=True)

    return df


def load_data() -> pd.DataFrame:
    path = Path(DATA_PATH)
    if path.exists():
        df = pd.read_csv(path, dtype=str)
        return _parse_raw(df)
    return pd.DataFrame(columns=COLUMNS + ["Dance Style"])


def save_data(df: pd.DataFrame) -> None:
    Path(DATA_PATH).parent.mkdir(parents=True, exist_ok=True)
    cols = [c for c in COLUMNS + ["Dance Style"] if c in df.columns]
    df[cols].to_csv(DATA_PATH, index=False)


def load_from_upload(uploaded_file) -> pd.DataFrame:
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        df = pd.read_csv(uploaded_file, dtype=str)
    else:
        df = pd.read_excel(uploaded_file, dtype=str)
    return _parse_raw(df)


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    cols = [c for c in COLUMNS + ["Dance Style"] if c in df.columns]
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df[cols].to_excel(writer, index=False, sheet_name="Practice Log")
    return buf.getvalue()


def add_entry(df: pd.DataFrame, entry: dict) -> pd.DataFrame:
    new_row = {col: "" for col in COLUMNS + ["Dance Style"]}
    new_row.update(entry)
    new_row["Priority"] = _normalize_priority(new_row.get("Priority", ""))
    new_row["Lesson Type"] = _normalize_lesson_type(new_row.get("Lesson Type", ""))
    new_row["Dance Style"] = _infer_style(new_row.get("Dance Type", ""))
    new_df = pd.concat([pd.DataFrame([new_row]), df], ignore_index=True)
    new_df["_sort_date"] = pd.to_datetime(new_df["Date"], dayfirst=False, errors="coerce")
    new_df = new_df.sort_values("_sort_date", ascending=False).drop(columns=["_sort_date"])
    new_df = new_df.reset_index(drop=True)
    return new_df


def filter_data(
    df: pd.DataFrame,
    years=None,
    months=None,
    instructors=None,
    priorities=None,
    lesson_types=None,
    dance_styles=None,
    dance_types=None,
    keyword: str = "",
) -> pd.DataFrame:
    result = df.copy()

    if years:
        result = result[result["Year"].astype(str).isin([str(y) for y in years])]

    if months:
        result = result[result["Month"].str.strip().isin(months)]

    if instructors:
        mask = result["Instructor(s)"].apply(
            lambda v: any(i.lower() in str(v).lower() for i in instructors)
        )
        result = result[mask]

    if priorities is not None and len(priorities) > 0:
        result = result[result["Priority"].isin(priorities)]

    if lesson_types:
        result = result[result["Lesson Type"].isin(lesson_types)]

    if dance_styles:
        mask = result["Dance Style"].apply(
            lambda v: any(ds.lower() in str(v).lower() for ds in dance_styles)
        )
        result = result[mask]

    if dance_types:
        mask = result["Dance Type"].apply(
            lambda v: any(dt.lower() in str(v).lower() for dt in dance_types)
        )
        result = result[mask]

    if keyword and keyword.strip():
        kw = keyword.strip().lower()
        text_cols = ["Instructor(s)", "Dance Type", "Lesson Type", "Note + Homework", "Reference", "Dance Style"]
        mask = result[text_cols].apply(
            lambda row: row.astype(str).str.lower().str.contains(kw, na=False).any(), axis=1
        )
        result = result[mask]

    return result
