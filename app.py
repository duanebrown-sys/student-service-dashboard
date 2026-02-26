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

# --- Load Data ---
data_path = os.path.join("data", "Service_Hours_Dashboard.xlsx")

if not os.path.exists(data_path):
    st.error(f"Could not find the data file at `{data_path}`. Make sure your Excel file is in the `data` folder and named exactly **Service Hours.xlsx**.")
    st.stop()

df = pd.read_excel(data_path)
df.columns = df.columns.str.strip()

# --- Search ---
search_query = st.text_input("🔍 Search by Name", placeholder="Start typing your name...")

if search_query:
    results = df[df["Student Name"].str.contains(search_query, case=False, na=False)]

    if results.empty:
        st.warning("No student found with that name. Double-check your spelling.")
    else:
        for _, row in results.iterrows():
            completed    = row["Completed Hours"]
            req_min      = row["Required Hours (Minimum)"]
            req_dist     = row["Required Hours (Distinction)"]
            out_min      = row["Outstanding Hours (Minimum)"]
            out_dist     = row["Outstanding Hours (Distinction)"]

            # Determine status
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
            st.markdown(f"<div class='big-name'>{row['Student Name']}</div>", unsafe_allow_html=True)
            st.caption(f"Grade {row['Grade']}")
            st.markdown(
                f"<span style='font-size:1.1rem; font-weight:600; color:{status_color}'>{status_label}</span>",
                unsafe_allow_html=True
            )

            st.write("")

            col1, col2, col3 = st.columns(3)
            col1.metric("Hours Completed", f"{completed} hrs")
            col2.metric("Minimum Required", f"{req_min} hrs")
            col3.metric("Distinction Level", f"{req_dist} hrs")

            st.write("")

            # Progress toward minimum
            pct_min = min(completed / req_min, 1.0) if req_min > 0 else 1.0
            st.write(f"**Progress toward Minimum** ({int(pct_min*100)}%)")
            st.progress(pct_min)

            # Progress toward distinction
            pct_dist = min(completed / req_dist, 1.0) if req_dist > 0 else 1.0
            st.write(f"**Progress toward Distinction** ({int(pct_dist*100)}%)")
            st.progress(pct_dist)

            if out_min > 0:
                st.info(f"You need **{out_min} more hours** to meet the minimum requirement.")
            elif out_dist > 0:
                st.info(f"Minimum requirement met! You need **{out_dist} more hours** to earn Distinction.")
            else:
                st.success("You have earned Distinction! Congratulations! 🎉")
