import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Student Service Hour Tracker", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .big-name { font-size: 1.5rem; font-weight: 700; margin-bottom: 0.25rem; }
    </style>
""", unsafe_allow_html=True)

st.title("🎓 Student Service Hour Tracker")
st.write("Enter your name below to see your service hour progress.")

# --- Load & Process Data ---
data_path = "Service_Hours.xlsx"

if not os.path.exists(data_path):
    st.error(f"Could not find `{data_path}`. Make sure it is in the same folder as app.py in your GitHub repo.")
    st.stop()

df = pd.read_excel(data_path)
df.columns = df.columns.str.strip()

# Combine the 4 student slots into one unified list
slots = [
    ("Name of student",   "Number of hours",   "Select student grade level", "Description of service",   "Date of service"),
    ("Name of student 2", "Number of hours 2",  "Select student grade level", "Description of service 2", "Date of service"),
    ("Name of student 3", "Number of hours 3",  "Select student grade level", "Description of service 3", "Date of service"),
    ("Name of student 4", "Number of hours 4",  "Select student grade level", "Description of service 4", "Date of service"),
]

records = []
for name_col, hours_col, grade_col, desc_col, date_col in slots:
    subset = df[[name_col, hours_col, grade_col, desc_col, date_col]].copy()
    subset.columns = ["Name", "Hours", "Grade", "Description", "Date"]
    records.append(subset)

combined = pd.concat(records)
combined = combined.dropna(subset=["Name"])
combined["Hours"]       = pd.to_numeric(combined["Hours"], errors="coerce").fillna(0)
combined["Name"]        = combined["Name"].str.strip().str.title()
combined["Description"] = combined["Description"].fillna("No description provided")
combined["Date"]        = pd.to_datetime(combined["Date"], errors="coerce")

# Summarize by student
summary = combined.groupby("Name").agg(
    Completed_Hours=("Hours", "sum"),
    Grade=("Grade", "first")
).reset_index()

# Requirements by grade
def get_requirements(grade):
    grade = str(grade).strip().lower().replace("th","").replace("st","").replace("nd","").replace("rd","")
    if grade in ["9", "10"]:
        return 50, 100
    elif grade in ["11", "12"]:
        return 100, 150
    else:
        return 50, 100

# --- Search ---
search_query = st.text_input("🔍 Search by Name", placeholder="Start typing your name...")

if search_query:
    results = summary[summary["Name"].str.contains(search_query, case=False, na=False)]

    if results.empty:
        st.warning("No student found with that name. Double-check your spelling.")
    else:
        for _, row in results.iterrows():
            completed = row["Completed_Hours"]
            grade     = row["Grade"]
            student_name = row["Name"]
            req_min, req_dist = get_requirements(grade)

            hours_needed_min  = max(0, req_min - completed)
            hours_needed_dist = max(0, req_dist - completed)

            # Status
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
            # Match using lowercase to avoid any casing mismatches
            student_log = combined[combined["Name"].str.lower() == student_name.lower()].copy()
            student_log = student_log.sort_values("Date", ascending=False)

            st.write("")
            with st.expander(f"📋 View Service Log ({len(student_log)} entries)"):
                if student_log.empty:
                    st.write("No entries found.")
                else:
                    for _, entry in student_log.iterrows():
                        date_str = entry["Date"].strftime("%B %d, %Y") if pd.notna(entry["Date"]) else "Date unknown"
                        hrs  = entry["Hours"]
                        desc = entry["Description"]
                        st.markdown(f"**{date_str}** — {hrs:.1f} hrs")
                        st.write(f"_{desc}_")
                        st.write("")
