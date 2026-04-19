import streamlit as st
import pandas as pd
import numpy as np
from model import HarvestEngine
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# --- DATABASE CONNECTION HELPER ---
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS")
    )

# Singleton Engine
if 'harvest_engine' not in st.session_state:
    st.session_state.harvest_engine = HarvestEngine()

st.set_page_config(page_title="AgriSmart Africa", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .main { background-color: #f9f7f2; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #2e7d32; }
    </style>
    """, unsafe_allow_html=True)

st.title("🌱 AgriSmart: Farm Decision Support")
st.markdown("### *Guidance for your next planting season based on soil and rain.*")

# --- SIDEBAR: FARM INPUTS ---
with st.sidebar:
    st.header("📍 Field Observations")
    st.info("Adjust the sliders to match your current soil test and local weather.")
    
    in_ph = st.sidebar.slider("Soil Acidity (pH)", 4.0, 9.0, 6.5, help="Test your soil to find this value.")
    in_rain = st.sidebar.slider("Expected Annual Rain (mm)", 300, 2000, 850)
    
    st.markdown("---")
    if st.button("🗑️ Reset Field Records"):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM farm_history;")
            conn.commit()
            cur.close()
            conn.close()
            st.success("Diary cleared!")
            st.rerun()
        except Exception as e:
            st.error(f"Error clearing history: {e}")

# --- HARVEST LOGIC & CONSTRAINT ANALYSIS ---
engine = st.session_state.harvest_engine
best_crop, strength, all_scores = engine.calculate_yield_potential(in_ph, in_rain)
# New: Get the expert reasoning for each crop
constraints = engine.analyze_constraints(in_ph, in_rain)

# --- VISUAL ADVICE ---
col1, col2 = st.columns([1, 1.5])

with col1:
    st.subheader("🌾 Recommended for your Land")
    st.metric(label="Best Crop to Plant", value=best_crop)
    
    if strength > 0.85:
        st.success(f"**Excellent Fit:** Conditions are nearly perfect for {best_crop}.")
    elif strength > 0.60:
        st.warning(f"**Fair Fit:** {best_crop} will grow, but may require soil management.")
    else:
        st.error("**Poor Fit:** We suggest checking for other land or improving soil quality.")

    if st.button("✅ Log this Planting Choice"):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            query = """INSERT INTO farm_history (soil_ph, rainfall_mm, recommended_crop, success_potential) 
                       VALUES (%s, %s, %s, %s)"""
            cur.execute(query, (float(in_ph), float(in_rain), str(best_crop), float(strength)))
            conn.commit()
            cur.close()
            conn.close()
            st.toast("Choice saved to farm history!")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to save record: {e}")

with col2:
    st.subheader("📊 Planting Options Comparison")
    chart_df = pd.DataFrame.from_dict(all_scores, orient='index', columns=['Planting Success Potential'])
    st.bar_chart(chart_df, color="#8d6e63")
    st.caption("A higher bar means the crop is more naturally suited to your soil and rain.")

# --- NEW: EXPLAINABLE AI SECTION (EXPERT INSIGHTS) ---
st.markdown("---")
st.subheader("🔎 Expert Agricultural Insights")
st.markdown("#### *Analysis of environmental stressors and risks per crop:*")

# Using columns to display the "Why" behind the math
insight_cols = st.columns(4)
for i, (crop, reasons) in enumerate(constraints.items()):
    with insight_cols[i]:
        st.markdown(f"**{crop}**")
        for r in reasons:
            if "too" in r.lower() or "risk" in r.lower() or "stress" in r.lower():
                st.write(f"⚠️ {r}")
            else:
                st.write(f"✅ {r}")

st.markdown("---")
st.subheader("📅 Your Farm's Planting Diary")

# --- SELECT LOGIC (The History Table) ---
try:
    conn = get_db_connection()
    query = "SELECT soil_ph, rainfall_mm, recommended_crop, success_potential, planting_season FROM farm_history ORDER BY planting_season DESC LIMIT 5"
    history_df = pd.read_sql(query, conn)
    conn.close()

    if not history_df.empty:
        history_df.columns = ['Soil pH', 'Rain (mm)', 'Crop Choice', 'Potential %', 'Date']
        history_df['Potential %'] = (history_df['Potential %'] * 100).round(1).astype(str) + '%'
        st.dataframe(history_df, use_container_width=True, hide_index=True)
    else:
        st.info("No records yet. Use the button above to log your first planting choice.")
except Exception as e:
    st.warning("Could not load farm history. Please check your database connection.")