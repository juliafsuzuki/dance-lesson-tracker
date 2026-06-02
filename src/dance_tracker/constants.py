INSTRUCTORS = ["Gerald", "Davit", "Cherry", "Rose", "Filemon"]

DANCE_STYLE_MAP = {
    "Waltz": "Smooth",
    "Tango": "Smooth",
    "Foxtrot": "Smooth",
    "Viennese Waltz": "Smooth",
    "Cha Cha": "Rhythm",
    "Rumba": "Rhythm",
    "Swing": "Rhythm",
    "Bolero": "Rhythm",
    "Mambo": "Rhythm",
    "A Whole New World": "Showcase",
    "Friend Like Me": "Showcase",
}

DANCE_STYLES = ["Smooth", "Rhythm", "Showcase"]

DANCES_BY_STYLE = {
    "Smooth": ["Waltz", "Tango", "Foxtrot", "Viennese Waltz"],
    "Rhythm": ["Cha Cha", "Rumba", "Swing", "Bolero", "Mambo"],
    "Showcase": ["A Whole New World", "Friend Like Me"],
}

ALL_DANCES = [d for dances in DANCES_BY_STYLE.values() for d in dances]

LESSON_TYPES = ["Private Lesson", "Coaching Lesson"]

PRIORITIES = ["High", "Low", ""]

COACHING_KEYWORDS = ["coaching"]

MONTHS_ORDER = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

DATA_PATH = "data/practice_log.csv"

COLUMNS = [
    "Year", "Month", "Day", "Date",
    "Instructor(s)", "Priority", "Lesson Type", "Dance Type",
    "Note + Homework", "Reference",
]
