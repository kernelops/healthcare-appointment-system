"""
Appointment Queue Dashboard
Real-time appointment management with urgency-based sorting
"""

import streamlit as st
from datetime import date, timedelta
from database.connection import initialize_pool
from services.appointment_service import (
    get_appointment_queue, get_appointment_statistics,
    get_all_specializations
)
from services.gemini_service import get_urgency_label, get_urgency_color
import time

# Page config
st.set_page_config(
    page_title="Appointment Queue",
    page_icon="📊",
    layout="wide"
)

# Initialize database
@st.cache_resource
def init_database():
    initialize_pool()
    return True

init_database()

# Custom CSS
st.markdown("""
    <style>
    .appointment-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: white;
    }
    .card-high {
        border-left: 5px solid #F44336;
        background-color: #FFEBEE;
    }
    .card-medium {
        border-left: 5px solid #FF9800;
        background-color: #FFF3E0;
    }
    .card-low {
        border-left: 5px solid #4CAF50;
        background-color: #E8F5E9;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.title("📊 Live Appointment Queue Dashboard")
st.markdown("**Real-time appointment tracking sorted by AI-calculated urgency**")
st.divider()

# Auto-refresh toggle
col_refresh1, col_refresh2 = st.columns([3, 1])

with col_refresh1:
    auto_refresh = st.checkbox("🔄 Enable auto-refresh (every 10 seconds)", value=False)

with col_refresh2:
    if st.button("🔃 Refresh Now", use_container_width=True):
        st.rerun()

# Auto-refresh logic
if auto_refresh:
    placeholder = st.empty()
    with placeholder.container():
        st.info("⏱️ Auto-refreshing... Next update in 10 seconds")
        time.sleep(10)
        st.rerun()

# Statistics
st.markdown("### 📈 Today's Statistics")

stats = get_appointment_statistics()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Appointments",
        value=stats.get('today_total', 0),
        delta="Today"
    )

with col2:
    st.metric(
        label="High Priority",
        value=stats.get('today_high_priority', 0),
        delta="Urgent cases",
        delta_color="inverse"
    )

with col3:
    active_doctors = len(set([s['spec_name'] for s in stats.get('specialization_distribution', [])]))
    st.metric(
        label="Active Specializations",
        value=active_doctors
    )

with col4:
    current_time = date.today().strftime("%B %d, %Y")
    st.metric(
        label="Date",
        value=current_time
    )

st.divider()

# Filters
st.markdown("### 🔍 Filter Appointments")

col_f1, col_f2, col_f3, col_f4 = st.columns(4)

with col_f1:
    date_options = {
        "Today": date.today(),
        "Tomorrow": date.today() + timedelta(days=1),
        "All Dates": None
    }
    selected_date_label = st.selectbox("📅 Date Filter", list(date_options.keys()))
    date_filter = date_options[selected_date_label]

with col_f2:
    urgency_filter = st.selectbox(
        "⚠️ Urgency Level",
        ["All", "High (8-10)", "Medium (4-7)", "Low (1-3)"]
    )
    urgency_filter_value = urgency_filter.split()[0] if urgency_filter != "All" else None

with col_f3:
    all_specs = ["All"] + get_all_specializations()
    spec_filter = st.selectbox("🏥 Specialization", all_specs)
    spec_filter_value = spec_filter if spec_filter != "All" else None

with col_f4:
    view_mode = st.selectbox("👁️ View", ["Cards", "Table"])

st.divider()

# Fetch appointments
appointments = get_appointment_queue(
    date_filter=date_filter,
    urgency_filter=urgency_filter_value,
    specialization_filter=spec_filter_value
)

# Display count
st.markdown(f"### 📋 Appointment Queue ({len(appointments)} appointments)")

if not appointments:
    st.info("ℹ️ No appointments found with the selected filters.")
else:
    # Group by urgency
    high_priority = [a for a in appointments if a['urgency_level'] >= 8]
    medium_priority = [a for a in appointments if 4 <= a['urgency_level'] < 8]
    low_priority = [a for a in appointments if a['urgency_level'] < 4]
    
    # Display based on view mode
    if view_mode == "Cards":
        # High Priority Section
        if high_priority:
            st.markdown("## 🔴 HIGH PRIORITY (Urgency 8-10)")
            st.markdown("*Requires immediate attention*")
            
            for i, apt in enumerate(high_priority, 1):
                with st.container():
                    st.markdown(f'<div class="appointment-card card-high">', unsafe_allow_html=True)
                    
                    col_a, col_b = st.columns([3, 1])
                    
                    with col_a:
                        st.markdown(f"### #{i} - {apt['appointment_code']}")
                        st.markdown(f"**👤 Patient:** {apt['patient_name']} ({apt['age']}, {apt['gender']})")
                        st.markdown(f"**📱 Phone:** {apt['phone']}")
                    
                    with col_b:
                        st.markdown(f"### 🔴 {apt['urgency_level']}/10")
                        st.markdown(f"**Status:** {apt['status']}")
                    
                    with st.expander("🩺 View Details"):
                        st.markdown(f"**Symptoms:**  \n{apt['symptom_text'][:200]}...")
                        st.markdown(f"**🤖 AI Diagnosis:** {apt['predicted_disease']} ({apt['probability']}%)")
                        st.markdown(f"**Urgency Reason:** {apt['urgency_reason']}")
                        st.markdown(f"**👨‍⚕️ Doctor:** Dr. {apt['doctor_name']} ({apt['specialization']})")
                        st.markdown(f"**📅 Scheduled:** {apt['appointment_date']} at {apt['appointment_time']}")
                        st.markdown(f"**💻 Mode:** {apt['mode']}")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
        
        # Medium Priority Section
        if medium_priority:
            st.markdown("---")
            st.markdown("## 🟡 MEDIUM PRIORITY (Urgency 4-7)")
            st.markdown("*Requires attention within 24-48 hours*")
            
            for i, apt in enumerate(medium_priority, 1):
                with st.container():
                    st.markdown(f'<div class="appointment-card card-medium">', unsafe_allow_html=True)
                    
                    col_a, col_b = st.columns([3, 1])
                    
                    with col_a:
                        st.markdown(f"### #{len(high_priority) + i} - {apt['appointment_code']}")
                        st.markdown(f"**👤 Patient:** {apt['patient_name']} ({apt['age']}, {apt['gender']})")
                    
                    with col_b:
                        st.markdown(f"### 🟡 {apt['urgency_level']}/10")
                    
                    with st.expander("🩺 View Details"):
                        st.markdown(f"**Symptoms:** {apt['symptom_text'][:150]}...")
                        st.markdown(f"**🤖 AI Diagnosis:** {apt['predicted_disease']} ({apt['probability']}%)")
                        st.markdown(f"**👨‍⚕️ Doctor:** Dr. {apt['doctor_name']} ({apt['specialization']})")
                        st.markdown(f"**📅 Scheduled:** {apt['appointment_date']} at {apt['appointment_time']}")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
        
        # Low Priority Section
        if low_priority:
            st.markdown("---")
            st.markdown("## 🟢 LOW PRIORITY (Urgency 1-3)")
            st.markdown("*Non-urgent, routine care*")
            
            for i, apt in enumerate(low_priority, 1):
                with st.container():
                    st.markdown(f'<div class="appointment-card card-low">', unsafe_allow_html=True)
                    
                    col_a, col_b = st.columns([3, 1])
                    
                    with col_a:
                        st.markdown(f"### #{len(high_priority) + len(medium_priority) + i} - {apt['appointment_code']}")
                        st.markdown(f"**👤 Patient:** {apt['patient_name']} | **🤖 Diagnosis:** {apt['predicted_disease']}")
                    
                    with col_b:
                        st.markdown(f"### 🟢 {apt['urgency_level']}/10")
                    
                    with st.expander("🩺 View Details"):
                        st.markdown(f"**👨‍⚕️ Doctor:** Dr. {apt['doctor_name']} ({apt['specialization']})")
                        st.markdown(f"**📅 Scheduled:** {apt['appointment_date']} at {apt['appointment_time']}")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
    
    else:  # Table view
        import pandas as pd
        
        # Create DataFrame
        df = pd.DataFrame(appointments)
        
        # Select and rename columns
        display_df = df[[
            'appointment_code', 'patient_name', 'age', 'urgency_level',
            'predicted_disease', 'doctor_name', 'specialization',
            'appointment_date', 'appointment_time', 'status'
        ]].copy()
        
        display_df.columns = [
            'ID', 'Patient', 'Age', 'Urgency', 'Diagnosis',
            'Doctor', 'Specialization', 'Date', 'Time', 'Status'
        ]
        
        # Color-code urgency
        def color_urgency(val):
            if val >= 8:
                return 'background-color: #FFEBEE'
            elif val >= 4:
                return 'background-color: #FFF3E0'
            else:
                return 'background-color: #E8F5E9'
        
        styled_df = display_df.style.applymap(color_urgency, subset=['Urgency'])
        
        st.dataframe(styled_df, use_container_width=True, height=600)

# SQL Query Display (for DBMS demonstration)
st.divider()

with st.expander("💾 View Database Query (DBMS Demonstration)"):
    st.markdown("### Complex JOIN Query Used")
    st.code("""
SELECT 
    a.appointment_id,
    a.appointment_date,
    a.appointment_time,
    a.urgency_level,
    p.full_name AS patient_name,
    p.age,
    p.gender,
    s.symptom_text,
    pred.predicted_disease,
    pred.probability,
    pred.urgency_reason,
    d.name AS doctor_name,
    spec.spec_name AS specialization
FROM appointments a
INNER JOIN patients p ON a.patient_id = p.patient_id
INNER JOIN symptoms s ON a.symptom_id = s.symptom_id
INNER JOIN predictions pred ON s.symptom_id = pred.symptom_id
INNER JOIN doctors d ON a.doctor_id = d.doctor_id
INNER JOIN specializations spec ON d.spec_id = spec.spec_id
WHERE a.status IN ('Confirmed', 'Pending')
ORDER BY a.urgency_level DESC, a.appointment_date ASC;
    """, language="sql")
    
    st.markdown("**DBMS Concepts Demonstrated:**")
    st.markdown("""
    - ✅ Multi-table JOINs (5 tables)
    - ✅ Foreign key relationships
    - ✅ Indexing on urgency_level (DESC) for performance
    - ✅ WHERE clause filtering
    - ✅ ORDER BY with multiple columns
    - ✅ Aggregate data retrieval
    """)

# Footer
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: #666;'>
    <p>Last updated: {date.today().strftime('%B %d, %Y')} | Auto-refresh: {'ON' if auto_refresh else 'OFF'}</p>
</div>
""", unsafe_allow_html=True)
