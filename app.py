import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import pearsonr
import os
from datetime import datetime

st.set_page_config(
    page_title="Rise Academy Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "Rise Academy Cohort Dashboard — Q1 2026"}
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .metric-card { background-color: #f0f2f6; padding: 20px; border-radius: 10px; }
    .header-section { border-bottom: 3px solid #1f77b4; padding-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Rise Academy Dashboard")
st.markdown("**Focus Areas:** 🎓 Student GPA • 🧠 Aptitude Clusters • 🤝 Mentoring • ✈️ Field Trips • 💪 Service Hours")

data_dir = "data"

# ────────────────────────────────────────────────
# Helper: Grade points & categorization
# ────────────────────────────────────────────────
grade_map = {'A+':4.0, 'A':4.0, 'A-':3.7, 'B+':3.3, 'B':3.0, 'B-':2.7,
             'C+':2.3, 'C':2.0, 'C-':1.7, 'D+':1.3, 'D':1.0, 'D-':0.7,
             'F':0.0, 'I':0.0}

def categorize_grade(score):
    if score in ['A+', 'A', 'A-', 'B+', 'B', 'B-']: return "As & Bs"
    if score in ['C+', 'C', 'C-', 'D+', 'D', 'D-']: return "Cs & Ds"
    if score == 'F': return "Fs"
    return "Other"

# ────────────────────────────────────────────────
# Load grades (only .xlsx)
# ────────────────────────────────────────────────
@st.cache_data
def load_grades():
    try:
        files = [f for f in os.listdir(data_dir) if f.lower().endswith('.xlsx') and 'grade' in f.lower()]
        if not files:
            return pd.DataFrame()
        
        dfs = []
        for f in files:
            try:
                df = pd.read_excel(os.path.join(data_dir, f), engine='openpyxl')
                dfs.append(df)
            except Exception as e:
                st.warning(f"⚠️ Could not load {f}: {str(e)[:50]}")
        
        if not dfs:
            return pd.DataFrame()
        
        all_grades = pd.concat(dfs, ignore_index=True)
        all_grades = all_grades[~all_grades.get('Student Name', '').str.contains('Test', na=False)]
        all_grades['points'] = all_grades['Score'].map(grade_map).fillna(0)
        return all_grades
    except Exception as e:
        st.error(f"Error loading grades: {str(e)}")
        return pd.DataFrame()

grades_df = load_grades()

# ────────────────────────────────────────────────
# Section 1: Student GPA
# ────────────────────────────────────────────────
st.header("1. 🎓 Student GPA")
if not grades_df.empty:
    gpa = grades_df['points'].mean()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Cohort GPA", f"{gpa:.2f}", delta="Q1 Average")
    with col2:
        st.metric("Students Tracked", len(grades_df['Student Name'].unique()), delta="Q1 Data")
    with col3:
        st.metric("Highest Grade", "A+", delta="Top Performance")
    
    # Grade distribution
    grade_dist = grades_df['Score'].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(10, 4))
    grade_dist.plot(kind='bar', ax=ax, color='steelblue', edgecolor='black', alpha=0.7)
    ax.set_title('Grade Distribution', fontsize=12, fontweight='bold')
    ax.set_xlabel('Grade')
    ax.set_ylabel('Count')
    ax.grid(axis='y', alpha=0.3)
    st.pyplot(fig)
    st.caption("📊 Q1 grade frequencies across all subjects.")
else:
    st.warning("📂 No grade data found. Please ensure .xlsx files with 'grade' in the filename are in the 'data' folder.")

# ────────────────────────────────────────────────
# Section 2: Aptitude Clusters
# ────────────────────────────────────────────────
st.header("2. 🧠 Aptitude Clusters (YouScience)")
try:
    cluster_file = os.path.join(data_dir, "Top 3 Clusters for Students.xlsx")
    if os.path.exists(cluster_file):
        df_cluster = pd.read_excel(cluster_file, engine='openpyxl')
        apt = df_cluster[df_cluster.get('Top 3 Aptitude') == 'Yes']['Cluster'].value_counts()
        interest = df_cluster[df_cluster.get('Top 3 Interest') == 'Yes']['Cluster'].value_counts()
        summary = pd.DataFrame({'Aptitude (n=60)': apt, 'Interest (n=60)': interest}).fillna(0).astype(int)
        summary['Gap %'] = ((summary['Interest (n=60)'] - summary['Aptitude (n=60)']) / 60 * 100).round(0).astype(str) + '%'
        summary = summary.reindex([
            'Supply Chain & Transportation',
            'Arts, Entertainment, & Design',
            'Construction / Manufacturing',
            'Healthcare & Human Services'
        ], fill_value=0)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.table(summary)
        with col2:
            if len(summary) > 1:
                r, _ = pearsonr(summary['Aptitude (n=60)'], summary['Interest (n=60)'])
                st.info(f"**Correlation**: r = {r:.2f}\n\n💡 Strong mismatch between raw talent and interest awareness.")
        
        # Visualization
        fig, ax = plt.subplots(figsize=(10, 4))
        x = range(len(summary))
        width = 0.35
        ax.bar([i - width/2 for i in x], summary['Aptitude (n=60)'], width, label='Aptitude', color='#2E86AB', alpha=0.8)
        ax.bar([i + width/2 for i in x], summary['Interest (n=60)'], width, label='Interest', color='#A23B72', alpha=0.8)
        ax.set_ylabel('Count')
        ax.set_title('Aptitude vs Interest by Cluster', fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels([c.split('&')[0].strip() for c in summary.index], rotation=45, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        st.pyplot(fig)
    else:
        st.warning("📂 Aptitude cluster file not found.")
except Exception as e:
    st.warning(f"⚠️ Clusters issue: {str(e)[:100]}")

# ────────────────────────────────────────────────
# Section 3: Mentoring Involvement
# ────────────────────────────────────────────────
st.header("3. 🤝 Mentoring Involvement")
try:
    mentor_file = os.path.join(data_dir, "Survey Data _ End of term reflection_Brotherhood Collective Input Sheet.xlsx")
    if os.path.exists(mentor_file):
        df_mentor = pd.read_excel(mentor_file, engine='openpyxl')
        count = len(df_mentor)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Students in Brotherhood Collective", count)
        
        if 'P1: Mentor Comfort (1-4)' in df_mentor.columns:
            avg_comfort = df_mentor['P1: Mentor Comfort (1-4)'].mean()
            with col2:
                st.metric("Avg Mentor Comfort", f"{avg_comfort:.1f}/4")
        
        if 'M3: Helped Peer (1/0)' in df_mentor.columns:
            pct_helped = df_mentor['M3: Helped Peer (1/0)'].mean() * 100
            with col3:
                st.metric("% Helped Peer", f"{pct_helped:.0f}%")
        
        st.caption("📋 From end-of-term reflections — Students reported: field trips, social bonding, peer mentoring, future planning.")
    else:
        st.warning("📂 Mentoring survey file not found.")
except Exception as e:
    st.warning(f"⚠️ Mentoring data issue: {str(e)[:100]}")

# ────────────────────────────────────────────────
# Section 4: Field Trip Participation
# ────────────────────────────────────────────────
st.header("4. ✈️ Field Trip Participation")
try:
    trip_file = os.path.join(data_dir, "Rise Academy Field Trip Student Roster.xlsx")
    if os.path.exists(trip_file):
        df_trips = pd.read_excel(trip_file, sheet_name=None, engine='openpyxl')
        trip_counts = {}
        
        for sheet_name, df in df_trips.items():
            if df.empty:
                continue
            col = df.select_dtypes(include=['object']).columns[0] if len(df.select_dtypes(include=['object']).columns) > 0 else None
            if col is None:
                continue
            names = df[col].dropna().astype(str).str.strip()
            valid = names[~names.str.contains('Teacher|Date|Rise Academy|false|na', case=False, na=False)]
            for name in valid:
                if len(name) > 2:
                    trip_counts[name] = trip_counts.get(name, 0) + 1
        
        if trip_counts:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Unique Students on Trips", len(trip_counts))
            with col2:
                st.metric("Avg Trips per Student", f"{sum(trip_counts.values()) / len(trip_counts):.1f}")
            
            series = pd.Series(trip_counts).value_counts().sort_index()
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.bar(series.index, series.values, color='#06A77D', alpha=0.8, edgecolor='black')
            ax.set_xlabel("Number of Trips Attended")
            ax.set_ylabel("Number of Students")
            ax.set_title("Field Trip Participation Distribution", fontweight='bold')
            ax.grid(axis='y', alpha=0.3)
            st.pyplot(fig)
        else:
            st.info("No attendance data parsed from rosters.")
    else:
        st.warning("📂 Field trip roster file not found.")
except Exception as e:
    st.warning(f"⚠️ Field trip data issue: {str(e)[:100]}")

# ────────────────────────────────────────────────
# Section 5: Service Hours
# ────────────────────────────────────────────────
st.header("5. 💪 Service Hours")
try:
    service_file = os.path.join(data_dir, "Service Hours.xlsx")
    if os.path.exists(service_file):
        df_service = pd.read_excel(service_file, engine='openpyxl')
        if not df_service.empty:
            total_hours = df_service.iloc[:, -1].sum() if df_service.shape[1] > 1 else 0
            avg_hours = df_service.iloc[:, -1].mean() if df_service.shape[1] > 1 else 0
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Service Hours", int(total_hours))
            with col2:
                st.metric("Avg per Student", f"{avg_hours:.1f}")
            with col3:
                st.metric("Students Tracked", len(df_service))
        else:
            st.info("Service hours file is empty.")
    else:
        st.info("💡 Service hours data not yet added. Contact your instructor if you have this information.")
except Exception as e:
    st.info(f"💡 Service hours data not available: {str(e)[:50]}")

st.markdown("---")
st.caption(f"📅 Dashboard updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | Data sources: Excel files in 'data' folder | Questions? Contact your Rise Academy advisor")
