import io
import pandas as pd
import streamlit as st
from engine import calculate_weighted_match_score, load_matching_rules

# Page configuration
st.set_page_config(
    page_title="TechZita Duplicate Inspector",
    page_icon="🔍",
    layout="wide",
)

# Sidebar setup
st.sidebar.image("logo.png", width=180)
st.sidebar.title("1. Data Ingestion")

data_source = st.sidebar.radio(
    "Data Source", ["CSV / Excel Upload", "SQL Database"]
)

uploaded_file = None
if data_source == "CSV / Excel Upload":
  st.sidebar.subheader("Upload dataset")
  uploaded_file = st.sidebar.file_uploader(
      "Upload", type=["csv", "xlsx"], label_visibility="collapsed"
  )
  st.sidebar.caption("200MB per file • CSV, XLSX")
else:
  st.sidebar.info("SQL Database connection configured via config/secrets.")

# Load Dataset First to Extract Columns for Rules Reference
df = None
if uploaded_file is not None:
  try:
    if uploaded_file.name.endswith(".csv"):
      df = pd.read_csv(uploaded_file)
    else:
      df = pd.read_excel(uploaded_file)
  except Exception as e:
    st.error(f"Error reading uploaded file: {e}")

# --- 2. MATCHING RULES SECTION ---
st.sidebar.markdown("---")
st.sidebar.title("2. Matching Rules")

custom_rules = {}

if df is not None:
  rule_input_method = st.sidebar.radio(
      "Rule Input Method",
      [
          "Interactive Multi-Field Selector",
          "Free Text Box",
          "Upload Rules File",
      ],
      horizontal=False,
  )

  all_columns = df.columns.tolist()

  if rule_input_method == "Interactive Multi-Field Selector":
    st.sidebar.write("Select fields and assign match weights:")
    selected_rule_columns = st.sidebar.multiselect(
        "Choose columns for rules",
        options=all_columns,
        default=all_columns[:2] if len(all_columns) >= 2 else all_columns,
    )

    for col in selected_rule_columns:
      weight = st.sidebar.slider(
          f"Weight for `{col}`",
          min_value=0.1,
          max_value=1.0,
          value=1.0,
          step=0.1,
          key=f"weight_{col}",
      )
      custom_rules[col] = weight

  elif rule_input_method == "Free Text Box":
    default_text = (
        "# Define rules (COLUMN_NAME: weight)\nCUSTOMER: 1.0\nADDR1: 0.8"
    )
    rule_text_area = st.sidebar.text_area(
        "Rules Configuration", value=default_text, height=130
    )

    if rule_text_area:
      for line in rule_text_area.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
          continue
        if ":" in line:
          col, weight = line.split(":", 1)
          try:
            custom_rules[col.strip()] = float(weight.strip())
          except ValueError:
            continue
  else:
    rule_file = st.sidebar.file_uploader("Upload Rules File (.txt)", type=["txt"])
    if rule_file is not None:
      custom_rules = load_matching_rules(rule_file)

  if custom_rules:
    st.sidebar.success(f"Active rules set for {len(custom_rules)} field(s)!")
else:
  st.sidebar.info("Upload a dataset to configure matching rules.")

# Main Content Dashboard
st.title("🔍 TechZita Duplicate Inspector")
st.subheader("Advanced Multi-Field Duplicate Detection & Graph Clustering Engine")
st.markdown("---")

if uploaded_file is None and data_source == "CSV / Excel Upload":
  st.info("👆 Please connect a database or upload a file from the sidebar to begin inspection.")
else:
  if df is not None:
    # Data Preview
    with st.expander("Preview Raw Dataset", expanded=False):
      st.dataframe(df.head(10), use_container_width=True)

    # Inspection Configuration Section
    st.markdown("### 3. Configure Inspection Fields")

    match_mode = st.radio(
        "Matching Mode",
        ["Single Column Matching", "Multi-Column Weighted Matching"],
        horizontal=True,
    )

    if match_mode == "Single Column Matching":
      selected_column = st.selectbox(
          "Select column to evaluate for duplicates", options=all_columns
      )
      ui_selected_columns = [selected_column] if selected_column else all_columns[:1]
    else:
      ui_selected_columns = st.multiselect(
          "Select columns to evaluate for duplicates",
          options=all_columns,
          default=all_columns[:3] if len(all_columns) >= 3 else all_columns,
      )

    threshold = st.slider(
        "Match Similarity Threshold (%)",
        min_value=50,
        max_value=100,
        value=85,
        step=1,
    )

    if st.button("Run Duplicate Inspection", type="primary"):
      # PRIORITY LOGIC: Check Section 2 rules first. If none exist, fallback to Section 3.
      if custom_rules:
        active_evaluation_columns = list(custom_rules.keys())
        evaluation_source = "Section 2 (Custom Matching Rules)"
      else:
        active_evaluation_columns = ui_selected_columns
        evaluation_source = "Section 3 (Configure Inspection Fields)"

      if not active_evaluation_columns:
        st.warning("Please specify inspection fields via Rules or Configuration.")
      else:
        st.success(
            f"Running duplicate inspection using **{evaluation_source}** "
            f"across {len(active_evaluation_columns)} field(s)..."
        )

        # Summary Metrics Dashboard
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Records", len(df))
        col2.metric("Evaluated Fields", len(active_evaluation_columns))
        col3.metric("Custom Rules Applied", len(custom_rules))
        col4.metric("Similarity Cutoff", f"{threshold}%")

        # Display applied evaluation source info
        st.info(f"Active Evaluation Source: **{evaluation_source}**")