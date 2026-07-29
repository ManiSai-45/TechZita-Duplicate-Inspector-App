"""
Data preprocessing and normalization pipeline.
"""
import re
import pandas as pd

class DataNormalizer:
    @staticmethod
    def clean_text(text: str) -> str:
        """Lowercases, strips, and removes special characters/extra whitespace."""
        if pd.isna(text) or text is None:
            return ""
        text = str(text).lower().strip()
        text = re.sub(r'[^a-z0-9\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text

    @staticmethod
    def normalize_phone(phone: str) -> str:
        """Strips non-numeric characters from phone numbers."""
        if pd.isna(phone) or phone is None:
            return ""
        return re.sub(r'\D', '', str(phone))

    @classmethod
    def preprocess_dataframe(cls, df: pd.DataFrame, text_cols: list = None, phone_cols: list = None) -> pd.DataFrame:
        """Applies normalization across specified columns."""
        norm_df = df.copy()
        
        if text_cols:
            for col in text_cols:
                if col in norm_df.columns:
                    norm_df[col + "_norm"] = norm_df[col].apply(cls.clean_text)
                    
        if phone_cols:
            for col in phone_cols:
                if col in norm_df.columns:
                    norm_df[col + "_norm"] = norm_df[col].apply(cls.normalize_phone)
                    
        return norm_df
