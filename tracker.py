import streamlit as st
import pandas as pd
import time
from datetime import datetime
import os
import plotly.express as px  # For nice charts

# --- Configuration ---
DATA_FILE = "study_history.csv"
st.set_page_config(page_title="StudyStack", page_icon="⏳", layout="wide")

# --- Helper Functions ---
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        # Ensure 'Breaks' column exists for older CSV files
        if 'Breaks' not in df.columns:
            df['Breaks'] = 0
        return df
    else:
        return pd.DataFrame(columns=["Date", "Subject", "Topic", "Duration_Minutes", "Breaks"])

def save_session(subject, topic, duration_minutes, breaks):
    df = load_data()
    new_entry = pd.DataFrame([{
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Subject": subject,
        "Topic": topic,
        "Duration_Minutes": round(duration_minutes, 2),
        "Breaks": breaks
    }])
    # Use concat to add the new row
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)

def format_time(seconds):
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02}:{m:02}:{s:02}"

# --- Session State Initialization ---
if 'time_left' not in st.session_state:
    st.session_state.time_left = 0
if 'timer_running' not in st.session_state:
    st.session_state.timer_running = False
if 'initial_time' not in st.session_state:
    st.session_state.initial_time = 0
if 'break_count' not in st.session_state:
    st.session_state.break_count = 0

# --- App Layout ---
st.title("⏳ StudyStack")

# Create Tabs
tab1, tab2 = st.tabs(["⏱️ Study Timer", "📊 Dashboard"])

# ==========================================
# TAB 1: STUDY TIMER
# ==========================================
with tab1:
    # Sidebar only appears here logic-wise, but visual is global
    with st.sidebar:
        st.header("📝 Session Setup")
        subject = st.text_input("Subject", value="General")
        topic = st.text_input("Topic", value="Study Session")
        
        st.write("### Set Duration")
        c1, c2 = st.columns(2)
        with c1: hours = st.number_input("Hours", 0, 24, 0)
        with c2: minutes = st.number_input("Minutes", 0, 59, 25)
        
        if st.button("Set / Reset Timer"):
            total_seconds = (hours * 3600) + (minutes * 60)
            st.session_state.time_left = total_seconds
            st.session_state.initial_time = total_seconds
            st.session_state.timer_running = False
            st.session_state.break_count = 0  # Reset breaks

    # Timer Display
    st.markdown(f"<h1 style='text-align: center; font-size: 80px;'>{format_time(st.session_state.time_left)}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center;'>Focusing on: <b>{subject} - {topic}</b> | Breaks taken: {st.session_state.break_count}</p>", unsafe_allow_html=True)

    # Progress Bar
    if st.session_state.initial_time > 0:
        prog = 1 - (st.session_state.time_left / st.session_state.initial_time)
        st.progress(min(prog, 1.0))
    else:
        st.progress(0)

    # Controls
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.session_state.timer_running:
            if st.button("⏸ Pause", use_container_width=True):
                st.session_state.timer_running = False
                st.session_state.break_count += 1 # Count the break!
                st.rerun()
        else:
            if st.button("▶ Start / Resume", use_container_width=True, type="primary"):
                st.session_state.timer_running = True
                st.rerun()

    # Timer Logic
    if st.session_state.timer_running:
        if st.session_state.time_left > 0:
            time.sleep(1)
            st.session_state.time_left -= 1
            st.rerun()
        else:
            st.session_state.timer_running = False
            st.balloons()
            save_session(subject, topic, st.session_state.initial_time / 60, st.session_state.break_count)
            st.session_state.time_left = 0
            st.session_state.initial_time = 0
            st.session_state.break_count = 0
            st.success("Session saved!")
            time.sleep(2)
            st.rerun()

# ==========================================
# TAB 2: DASHBOARD
# ==========================================
with tab2:
    st.header("📈 Study Analytics")
    
    df = load_data()
    
    if not df.empty:
        # 1. Top Level Metrics
        total_time = df['Duration_Minutes'].sum()
        total_sessions = len(df)
        avg_time = df['Duration_Minutes'].mean()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Study Hours", f"{total_time/60:.1f} h")
        m2.metric("Total Sessions", total_sessions)
        m3.metric("Avg Session Length", f"{avg_time:.0f} min")
        
        st.divider()
        
        # 2. Extremes (Longest, Shortest, Most Breaks)
        st.subheader("🏆 Records")
        c1, c2, c3 = st.columns(3)
        
        # Longest Session
        longest = df.loc[df['Duration_Minutes'].idxmax()]
        c1.info(f"**Longest Session**\n\n{longest['Subject']} ({longest['Duration_Minutes']} min)")
        
        # Shortest Session
        shortest = df.loc[df['Duration_Minutes'].idxmin()]
        c2.warning(f"**Shortest Session**\n\n{shortest['Subject']} ({shortest['Duration_Minutes']} min)")
        
        # Most Breaks
        if df['Breaks'].sum() > 0:
            most_breaks = df.loc[df['Breaks'].idxmax()]
            c3.error(f"**Most Distracted**\n\n{most_breaks['Subject']} ({most_breaks['Breaks']} breaks)")
        else:
            c3.success("**Most Distracted**\n\nNo breaks recorded yet!")

        st.divider()

        # 3. Subject Breakdown (Most & Least Studied)
        col_charts1, col_charts2 = st.columns(2)
        
        with col_charts1:
            st.subheader("📚 Time by Subject")
            subject_stats = df.groupby("Subject")["Duration_Minutes"].sum().sort_values(ascending=True)
            st.bar_chart(subject_stats)
            
            # Identify Most/Least
            most_studied_sub = subject_stats.idxmax()
            least_studied_sub = subject_stats.idxmin()
            st.caption(f"Most studied: **{most_studied_sub}** | Least studied: **{least_studied_sub}**")

        with col_charts2:
            st.subheader("📖 Time by Topic")
            topic_stats = df.groupby("Topic")["Duration_Minutes"].sum().sort_values(ascending=True).tail(5) # Show top 5
            st.bar_chart(topic_stats)
            st.caption("Top 5 Topics shown")

        # 4. Raw Data Table
        with st.expander("View Full History Data"):
            st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)
            
    else:
        st.info("No study data available yet. Complete a session in the 'Timer' tab!")