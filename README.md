# Advanced Enterprise Duplicate Detection & Graph Clustering System

An upgraded, production-ready system for identifying, scoring, and grouping duplicate records across SQL databases and tabular files.

## Upgraded Capabilities

1. **Text Normalization Pipeline (`normalizer.py`)**: Automatic string cleaning, lowercasing, non-alphanumeric character removal, and extra whitespace stripping prior to matching.
2. **Weighted Multi-Field Scoring (`engine.py`)**: Assign custom relative importance (weights 1–10) per field to generate a unified **Composite Similarity Score (%)**.
3. **Graph-Based Duplicate Clustering (`networkx`)**: Group connected duplicate pairs into unified `Cluster_ID` families (`CLUSTER_001`, `CLUSTER_002`) and automatically flag designated **Master Records** based on data completeness.
4. **Enhanced Analytics UI**: Visualize cluster size distributions, composite scores, master flags, and download clean datasets.

## How to Run

1. **Extract Zip**: Unzip `duplicate_detection_app_v2.zip`.
2. **Activate Environment & Install Dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Launch Web App**:
   ```bash
   streamlit run app.py
   ```
