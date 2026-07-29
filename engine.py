"""
Optimized Advanced Duplicate Detection Engine with Blocking, Multi-Column Combination,
and Weighted Scoring Support.
"""
import pandas as pd
import networkx as nx
from rapidfuzz import fuzz
from typing import List, Dict, Tuple
from normalizer import DataNormalizer
from collections import defaultdict

class AdvancedDuplicateEngine:
    def __init__(self, df: pd.DataFrame):
        self.original_df = df.copy()
        self.df = df.copy()

    def _normalize_data(self, rules: List[Dict]) -> pd.DataFrame:
        """Preprocesses columns, combined fields, and manual text inputs based on rules."""
        norm_df = self.df.copy()
        for i, r in enumerate(rules):
            col_target = r["column"]
            is_manual = r.get("is_manual", False)
            rule_key = f"rule_field_{i}"
            
            if is_manual:
                # If manual text input, treat the string as a constant or lookup value across rows
                norm_df[rule_key + "_norm"] = DataNormalizer.clean_text(str(col_target))
            elif isinstance(col_target, list) and len(col_target) > 0:
                # Combine multiple columns with a space separator
                combined_series = norm_df[col_target].astype(str).agg(' '.join, axis=1)
                norm_df[rule_key + "_norm"] = combined_series.apply(DataNormalizer.clean_text)
            else:
                col_name = str(col_target)
                if col_name in norm_df.columns:
                    norm_df[rule_key + "_norm"] = norm_df[col_name].apply(DataNormalizer.clean_text)
                else:
                    norm_df[rule_key + "_norm"] = ""
            
            r["active_norm_col"] = rule_key + "_norm"
        return norm_df

    def run_detection(self, rules: List[Dict], composite_threshold: float = 80.0) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Executes high-speed weighted duplicate detection using blocking strategy.
        """
        if self.df.empty:
            return self.df, self.df, pd.DataFrame()

        norm_df = self._normalize_data(rules)
        records = norm_df.to_dict("records")
        num_records = len(records)

        # Normalize weights
        total_weight = sum(r.get("weight", 1.0) for r in rules)
        for r in rules:
            r["normalized_weight"] = r.get("weight", 1.0) / (total_weight if total_weight > 0 else 1)

        # Blocking Strategy for High-Speed Performance
        blocks = defaultdict(list)
        first_rule_col = rules[0]["active_norm_col"] if rules else None

        for idx, record in enumerate(records):
            val = record.get(first_rule_col, "")
            block_key = val[:2] if len(val) >= 2 else "gen"
            blocks[block_key].append(idx)

        matched_pairs = set()
        pair_scores = {}

        for block_key, indices in blocks.items():
            block_len = len(indices)
            for x in range(block_len):
                for y in range(x + 1, block_len):
                    i = indices[x]
                    j = indices[y]
                    
                    composite_score = 0.0
                    for rule in rules:
                        col_norm = rule["active_norm_col"]
                        val1 = records[i].get(col_norm, "")
                        val2 = records[j].get(col_norm, "")

                        if rule["type"] == "Exact Match":
                            field_score = 100.0 if (val1 == val2 and val1 != "") else 0.0
                        else:
                            field_score = float(fuzz.token_sort_ratio(val1, val2)) if (val1 and val2) else 0.0

                        composite_score += field_score * rule["normalized_weight"]

                    if composite_score >= composite_threshold:
                        pair_key = (min(i, j), max(i, j))
                        matched_pairs.add(pair_key)
                        pair_scores[pair_key] = round(composite_score, 2)

        # Graph-Based Clustering
        G = nx.Graph()
        G.add_nodes_from(range(num_records))
        G.add_edges_from(list(matched_pairs))

        clusters = [c for c in nx.connected_components(G) if len(c) > 1]

        output_df = self.original_df.copy()
        output_df["Cluster_ID"] = None
        output_df["Is_Master"] = False
        output_df["Match_Score"] = 100.0

        duplicate_indices = set()
        cluster_summaries = []

        for idx, cluster_nodes in enumerate(clusters, start=1):
            cluster_id = f"CLUSTER_{idx:03d}"
            nodes_list = sorted(list(cluster_nodes))
            
            master_idx = min(nodes_list, key=lambda x: output_df.iloc[x].isna().sum())

            output_df.loc[nodes_list, "Cluster_ID"] = cluster_id
            output_df.loc[master_idx, "Is_Master"] = True

            for node in nodes_list:
                duplicate_indices.add(node)
                if node != master_idx:
                    pair_key = (min(master_idx, node), max(master_idx, node))
                    output_df.loc[node, "Match_Score"] = pair_scores.get(pair_key, composite_threshold)

            cluster_summaries.append({
                "Cluster ID": cluster_id,
                "Cluster Size": len(nodes_list),
                "Master Record ID": master_idx,
                "Member Row Indices": str(nodes_list)
            })

        duplicates_df = output_df[output_df.index.isin(duplicate_indices)].copy()
        clean_df = output_df[~output_df.index.isin(duplicate_indices)].copy()
        cluster_summary_df = pd.DataFrame(cluster_summaries)

        return clean_df, duplicates_df, cluster_summary_df