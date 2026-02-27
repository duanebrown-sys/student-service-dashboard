import streamlit as st
import pandas as pd

st.set_page_config(page_title="Student Service Hour Tracker", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .big-name { font-size: 1.5rem; font-weight: 700; margin-bottom: 0.25rem; }
    .gold   { color: #FFD700; font-size: 1.3rem; }
    .silver { color: #C0C0C0; font-size: 1.3rem; }
    .bronze { color: #CD7F32; font-size: 1.3rem; }
    </style>
""", unsafe_allow_html=True)

st.title("🎓 Student Service Hour Tracker")
st.write("Enter your name below to see your service hour progress.")

# --- Load Live Data from Google Sheet ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSW8n1nHKhUpvA1jcDBswmKuHQ_QkRXrZHq7Enbjb1TtzAifFX_GDQXgy3o45oBzXJhPydfU8NAKopd/pub?output=csv"

@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = df.columns.str.strip()

    slots = [
        ("Name of student",   "Number of hours",   "Select student grade level", "Description of service",   "Date of service"),
        ("Name of student.1", "Number of hours.1", "Select student grade level", "Description of service.1", "Date of service"),
        ("Name of student.2", "Number of hours.2", "Select student grade level", "Description of service.2", "Date of service"),
        ("Name of student.3", "Number of hours.3", "Select student grade level", "Description of service.3", "Date of service"),
    ]

    records = []
    for name_col, hours_col, grade_col, desc_col, date_col in slots:
        if name_col in df.columns:
            subset = df[[name_col, hours_col, grade_col, desc_col, date_col]].copy()
            subset.columns = ["Name", "Hours", "Grade", "Description", "Date"]
            records.append(subset)

    combined = pd.concat(records)
    combined = combined.dropna(subset=["Name"])
    combined["Hours"]       = pd.to_numeric(combined["Hours"], errors="coerce").fillna(0)
    combined["Name"]        = combined["Name"].str.strip().str.title()
    combined["Description"] = combined["Description"].fillna("No description provided")
    combined["Date"]        = pd.to_datetime(combined["Date"], errors="coerce")

    summary = combined.groupby("Name").agg(
        Completed_Hours=("Hours", "sum"),
        Grade=("Grade", "first")
    ).reset_index()

    return combined, summary

try:
    combined, summary = load_data()
except Exception as e:
    st.error(f"Could not load data from Google Sheets. Error: {e}")
    st.stop()

# --- Requirements by grade ---
def get_requirements(grade):
    grade = str(grade).strip().lower().replace("th","").replace("st","").replace("nd","").replace("rd","")
    if grade in ["9", "10"]:
        return 50, 100
    elif grade in ["11", "12"]:
        return 100, 150
    else:
        return 50, 100

# --- Leaderboard ---
st.subheader("🏆 Leaderboard — Top 5 Closest to Completion")

leaderboard = summary.copy()
leaderboard[["req_min", "req_dist"]] = leaderboard["Grade"].apply(
    lambda g: pd.Series(get_requirements(g))
)
leaderboard["pct_min"] = (leaderboard["Completed_Hours"] / leaderboard["req_min"] * 100).clip(upper=100)
leaderboard["hours_remaining"] = (leaderboard["req_min"] - leaderboard["Completed_Hours"]).clip(lower=0)

# Only show students not yet at minimum, sorted by closest to finish
not_done = leaderboard[leaderboard["hours_remaining"] > 0].sort_values("hours_remaining").head(5)

medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

for i, (_, row) in enumerate(not_done.iterrows()):
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown(f"{medals[i]} **{row['Name']}** — Grade {row['Grade']}")
        st.progress(row["pct_min"] / 100)
    with col2:
        st.metric("Hours Completed", f"{row['Completed_Hours']:.1f} hrs")
        st.caption(f"⏳ {row['hours_remaining']:.1f} hrs to go")

st.divider()

# --- Search ---
st.subheader("🔍 Check Your Progress")
search_query = st.text_input("Search by Name", placeholder="Start typing your name...")

if search_query:
    results = summary[summary["Name"].str.contains(search_query, case=False, na=False)]

    if results.empty:
        st.warning("No student found with that name. Double-check your spelling.")
    else:
        for _, row in results.iterrows():
            completed    = row["Completed_Hours"]
            grade        = row["Grade"]
            student_name = row["Name"]
            req_min, req_dist = get_requirements(grade)

            hours_needed_min  = max(0, req_min - completed)
            hours_needed_dist = max(0, req_dist - completed)

            if completed >= req_dist:
                status_label = "🏆 Distinction"
                status_color = "#2e7d32"
            elif completed >= req_min:
                status_label = "✅ Requirement Met"
                status_color = "#1565c0"
            else:
                status_label = "⏳ In Progress"
                status_color = "#e65100"

            st.divider()
            st.markdown(f"<div class='big-name'>{student_name}</div>", unsafe_allow_html=True)
            st.caption(f"Grade {grade}")
            st.markdown(
                f"<span style='font-size:1.1rem; font-weight:600; color:{status_color}'>{status_label}</span>",
                unsafe_allow_html=True
            )

            st.write("")

            col1, col2, col3 = st.columns(3)
            col1.metric("Hours Completed", f"{completed:.1f} hrs")
            col2.metric("Minimum Required", f"{req_min} hrs")
            col3.metric("Distinction Level", f"{req_dist} hrs")

            st.write("")

            pct_min = min(completed / req_min, 1.0) if req_min > 0 else 1.0
            st.write(f"**Progress toward Minimum** ({int(pct_min * 100)}%)")
            st.progress(pct_min)

            pct_dist = min(completed / req_dist, 1.0) if req_dist > 0 else 1.0
            st.write(f"**Progress toward Distinction** ({int(pct_dist * 100)}%)")
            st.progress(pct_dist)

            st.write("")
            if hours_needed_min > 0:
                st.info(f"You need **{hours_needed_min:.1f} more hours** to meet the minimum requirement.")
            elif hours_needed_dist > 0:
                st.info(f"Minimum met! You need **{hours_needed_dist:.1f} more hours** to earn Distinction.")
            else:
                st.success("You have earned Distinction! Congratulations! 🎉")

            # --- Service Log ---
            student_log = combined[combined["Name"].str.lower() == student_name.lower()].copy()
            student_log = student_log.sort_values("Date", ascending=False)

            st.write("")
            with st.expander(f"📋 View Service Log ({len(student_log)} entries)"):
                if student_log.empty:
                    st.write("No entries found.")
                else:
                    for _, entry in student_log.iterrows():
                        date_str = entry["Date"].strftime("%B %d, %Y") if pd.notna(entry["Date"]) else "Date unknown"
                        st.markdown(f"**{date_str}** — {entry['Hours']:.1f} hrs")
                        st.write(f"_{entry['Description']}_")
                        st.write("")
