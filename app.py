"""
TechZIta Duplicate Inspector - Modern Streamlit Interface featuring Custom CSS, 
Collapsible Rule Expanders, High-Speed Settings, and CSV/Excel Downloads.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import io

from config import DEFAULT_FUZZY_THRESHOLD, COMPOSITE_SCORE_THRESHOLD, COLOR_CLEAN, COLOR_DUPLICATE
from db_connector import DatabaseManager
from engine import AdvancedDuplicateEngine

# Page Configuration
st.set_page_config(page_title="TechZIta Duplicate Inspector", layout="wide", page_icon="🔎")

# Custom UI Styling (Modern Dark Dashboard Look)
st.markdown("""
    <style>
        .main {
            background-color: #0e1117;
        }
        div[data-testid="stMetric"] {
            background-color: #1a1c24;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #2d3748;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: #1a1c24;
            border-radius: 8px 8px 0px 0px;
            padding: 10px 20px;
            color: #ffffff;
            font-weight: 600;
        }
    </style>
""", unsafe_allow_html=True)

def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

# -----------------------------------------------------------------------------
# SIDEBAR: LOGO & DATA INGESTION
# -----------------------------------------------------------------------------
try:
    st.sidebar.image("logo.png", use_container_width=True)
except Exception:
    pass  # Fallback if logo.png is missing

st.sidebar.markdown("---")
st.sidebar.header("📁 1. Data Ingestion")
source_type = st.sidebar.radio("Data Source", ["CSV / Excel Upload", "SQL Database"])

df = None
active_conn_str = None

if source_type == "CSV / Excel Upload":
    file = st.sidebar.file_uploader("Upload dataset", type=["csv", "xlsx"])
    if file:
        try:
            df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
            st.sidebar.success(f"Successfully loaded {len(df):,} records.")
        except Exception as err:
            st.sidebar.error(f"Error loading file: {err}")
else:
    db_engine = st.sidebar.selectbox("Engine", ["SQLite", "PostgreSQL", "MySQL"])
    if db_engine == "SQLite":
        db_path = st.sidebar.text_input("Database Path", "data.db")
        active_conn_str = DatabaseManager.build_connection_string("sqlite", "", "", "", "", "", sqlite_path=db_path)
    else:
        host = st.sidebar.text_input("Host", "localhost")
        port = st.sidebar.text_input("Port", "5432" if db_engine == "PostgreSQL" else "3306")
        db_name = st.sidebar.text_input("Database Name")
        user = st.sidebar.text_input("Username")
        pwd = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Connect"):
            active_conn_str = DatabaseManager.build_connection_string(db_engine, host, port, db_name, user, pwd)

    query = st.sidebar.text_area("SQL Query", "SELECT * FROM customers LIMIT 1000")
    if st.sidebar.button("Execute Query") and active_conn_str:
        try:
            df = DatabaseManager.fetch_data(active_conn_str, query)
            st.sidebar.success(f"Fetched {len(df):,} records.")
        except Exception as err:
            st.sidebar.error(f"SQL Error: {err}")

# -----------------------------------------------------------------------------
# MAIN DASHBOARD HEADER
# -----------------------------------------------------------------------------
st.title("🔎 TechZIta Duplicate Inspector")
st.markdown("##### Advanced Multi-Field Duplicate Detection & Graph Clustering Engine")
st.markdown("---")

if df is not None:
    # Dataset Preview Section
    with st.expander("📋 View Dataset Preview (First 10 Rows)", expanded=False):
        st.dataframe(df.head(10), use_container_width=True)

    # Rule Configuration Section inside an Expander for a clean look
    rules = []
    cols = list(df.columns)
    
    with st.expander("⚙️ Configure Rules, Field Combinations & Manual Criteria", expanded=True):
        custom_rules_enabled = st.checkbox("Enable Custom Field Weights & Rules", value=True)

        if custom_rules_enabled:
            rule_count = st.number_input("Number of Rules to Define", min_value=1, max_value=10, value=min(2, len(cols)))
            
            for i in range(int(rule_count)):
                st.markdown(f"**Rule #{i+1} Setup**")
                r_mode = st.radio(f"Selection Mode #{i+1}", ["Single Column", "Combine Multiple Columns", "Manual Custom Text Input"], horizontal=True, key=f"mode_{i}")
                
                r1, r2, r3 = st.columns([3, 3, 2])
                with r1:
                    if r_mode == "Single Column":
                        target_col = st.selectbox(f"Column #{i+1}", cols, key=f"col_{i}")
                    elif r_mode == "Combine Multiple Columns":
                        target_col = st.multiselect(f"Select Columns #{i+1}", cols, key=f"multi_col_{i}")
                    else:
                        target_col = st.text_input(f"Custom Text #{i+1}", value="", key=f"manual_text_{i}")
                        
                with r2:
                    m_type = st.selectbox(f"Match Type #{i+1}", ["Fuzzy Match", "Exact Match"], key=f"type_{i}")
                with r3:
                    weight = st.slider(f"Weight #{i+1}", 1, 10, 5, key=f"w_{i}")
                
                if target_col is not None and target_col != "":
                    rules.append({
                        "column": target_col, 
                        "type": m_type, 
                        "weight": weight, 
                        "is_manual": (r_mode == "Manual Custom Text Input")
                    })
                st.markdown("---")

            st.markdown("#### Overall Threshold Settings")
            composite_threshold = st.slider("Minimum Composite Match Score (%)", 50, 100, COMPOSITE_SCORE_THRESHOLD)

        else:
            st.info("⚡ Default Mode: Equal weighting across selected columns.")
            selected = st.multiselect("Columns to compare:", cols, default=cols)
            composite_threshold = COMPOSITE_SCORE_THRESHOLD
            for c in selected:
                rules.append({"column": c, "type": "Exact Match", "weight": 1, "is_manual": False})

    # Execution Button
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        run_process = st.button("🚀 Process & Cluster Duplicates", type="primary", use_container_width=True)

    if run_process and rules:
        with st.spinner("Running high-speed matching engine, scoring, and clustering..."):
            engine = AdvancedDuplicateEngine(df)
            clean_df, duplicate_df, cluster_summary_df = engine.run_detection(rules, composite_threshold=composite_threshold)

            st.markdown("---")
            st.subheader("📊 Execution & Quality Report")

            total_rec = len(df)
            dup_rec = len(duplicate_df)
            clean_rec = len(clean_df)
            total_clusters = len(cluster_summary_df)

            # Modern Metric Cards
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Total Records", f"{total_rec:,}")
            k2.metric("Clean Records", f"{clean_rec:,}")
            k3.metric("Duplicate Records", f"{dup_rec:,}")
            k4.metric("Cluster Groups", f"{total_clusters:,}")

            st.markdown("<br>", unsafe_allow_html=True)

            # Visualizations
            c1, c2 = st.columns(2)
            with c1:
                fig = px.pie(
                    names=["Clean Data", "Duplicates"], 
                    values=[clean_rec, dup_rec], 
                    color_discrete_sequence=[COLOR_CLEAN, COLOR_DUPLICATE],
                    title="Clean vs Duplicate Ratio"
                )
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
                st.plotly_chart(fig, use_container_width=True)

            with c2:
                if not cluster_summary_df.empty:
                    fig_hist = px.bar(
                        cluster_summary_df.head(15), 
                        x="Cluster ID", 
                        y="Cluster Size",
                        title="Top Duplicate Cluster Sizes",
                        color_discrete_sequence=["#3498DB"]
                    )
                    fig_hist.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
                    st.plotly_chart(fig_hist, use_container_width=True)

            st.markdown("---")

            # Structured Tabs for Output Data
            t_clusters, t_dups, t_clean = st.tabs(["📌 Graph Cluster Summary", "⚠️ Flagged Duplicates", "✅ Clean Data Output"])

            with t_clusters:
                st.markdown("### Duplicate Groups (Clusters)")
                st.dataframe(cluster_summary_df, use_container_width=True)

            with t_dups:
                st.markdown("### Identified Duplicates with Master Flags")
                st.dataframe(duplicate_df, use_container_width=True)
                if not duplicate_df.empty:
                    st.markdown("**Download Reports:**")
                    d1, d2 = st.columns(2)
                    with d1:
                        st.download_button("📥 Download Duplicates (CSV)", duplicate_df.to_csv(index=False), "duplicate_report.csv", "text/csv", use_container_width=True)
                    with d2:
                        excel_dup = convert_df_to_excel(duplicate_df)
                        st.download_button("📥 Download Duplicates (Excel)", excel_dup, "duplicate_report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

            with t_clean:
                st.markdown("### Clean Data Output")
                st.dataframe(clean_df, use_container_width=True)
                st.markdown("**Download Cleaned Data:**")
                c1, c2 = st.columns(2)
                with c1:
                    st.download_button("📥 Download Clean Data (CSV)", clean_df.to_csv(index=False), "cleaned_data.csv", "text/csv", use_container_width=True)
                with c2:
                    excel_clean = convert_df_to_excel(clean_df)
                    st.download_button("📥 Download Clean Data (Excel)", excel_clean, "cleaned_data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

else:
    st.info("👈 Please connect a database or upload a file from the sidebar to begin inspection.")