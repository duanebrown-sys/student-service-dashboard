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

# Combine the 4 student slots into one unified list of (name, hours, grade)
slots = [
    ("Name of student",   "Number of hours",   "Select student grade level"),
    ("Name of student 2", "Number of hours 2",  "Select student grade level"),
    ("Name of student 3", "Number of hours 3",  "Select student grade level"),
    ("Name of student 4", "Number of hours 4",  "Select student grade level"),
]

records = []
for name_col, hours_col, grade_col in slots:
    subset = df[[name_col, hours_col, grade_col]].copy()
    subset.columns = ["Name", "Hours", "Grade"]
    records.append(subset)

combined = pd.concat(records)
combined = combined.dropna(subset=["Name"])
combined["Hours"] = pd.to_numeric(combined["Hours"], errors="coerce").fillna(0)
combined["Name"]  = combined["Name"].str.strip().str.title()

# Summarize by student
summary = combined.groupby("Name").agg(
    Completed_Hours=("Hours", "sum"),
    Grade=("Grade", "first")
).reset_index()

# Requirements by grade
def get_requirements(grade):
    grade = str(grade).strip().lower().replace("th", "").replace("st", "").replace("nd", "").replace("rd", "")
    if grade in ["9", "10"]:
        return 50, 100
    elif grade in ["11", "12"]:
        return 100, 150
    else:
        return 50, 100  # default fallback

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
            st.markdown(f"<div class='big-name'>{row['Name']}</div>", unsafe_allow_html=True)
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

            # Progress toward minimum
            pct_min = min(completed / req_min, 1.0) if req_min > 0 else 1.0
            st.write(f"**Progress toward Minimum** ({int(pct_min * 100)}%)")
            st.progress(pct_min)

            # Progress toward distinction
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
