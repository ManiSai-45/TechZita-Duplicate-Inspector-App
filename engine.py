import io
import pandas as pd
from rapidfuzz import fuzz


def load_matching_rules(uploaded_rule_file):
  """Parses an external text-based rules file mapping column names to match weights.

  Example format in txt: first_name: 1.0 last_name: 0.8 email: 1.0
  """
  rules = {}
  if uploaded_rule_file is None:
    return rules

  try:
    if isinstance(uploaded_rule_file, io.IOBase):
      lines = uploaded_rule_file.readlines()
    else:
      lines = uploaded_rule_file.getvalue().decode("utf-8").splitlines()

    for line in lines:
      if isinstance(line, bytes):
        line = line.decode("utf-8")
      line = line.strip()

      if not line or line.startswith("#"):
        continue

      if ":" in line:
        col, weight = line.split(":", 1)
        try:
          rules[col.strip()] = float(weight.strip())
        except ValueError:
          continue
  except Exception:
    pass

  return rules


def calculate_weighted_match_score(row1, row2, selected_columns, rules=None):
  """Calculates a weighted match score across multiple selected columns

  based on custom or default rules.
  """
  if rules is None:
    rules = {}

  total_weight = 0.0
  weighted_score_sum = 0.0

  for col in selected_columns:
    val1 = str(row1.get(col, ""))
    val2 = str(row2.get(col, ""))

    similarity = fuzz.token_sort_ratio(val1, val2)
    weight = rules.get(col, 1.0)

    weighted_score_sum += similarity * weight
    total_weight += weight

  if total_weight == 0:
    return 0.0

  return weighted_score_sum / total_weight