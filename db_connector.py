"""
Database abstraction layer to handle SQL connections.
"""
from sqlalchemy import create_engine
import pandas as pd

class DatabaseManager:
    @staticmethod
    def build_connection_string(db_type: str, host: str, port: str, db_name: str, user: str, password: str, sqlite_path: str = "app.db") -> str:
        if db_type.lower() == "sqlite":
            return f"sqlite:///{sqlite_path}"
        elif db_type.lower() == "postgresql":
            return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
        elif db_type.lower() == "mysql":
            return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    @classmethod
    def fetch_data(cls, connection_string: str, query: str) -> pd.DataFrame:
        engine = create_engine(connection_string)
        with engine.connect() as conn:
            return pd.read_sql(query, conn)
            
    @classmethod
    def write_data(cls, connection_string: str, df: pd.DataFrame, table_name: str, if_exists: str = "append") -> bool:
        engine = create_engine(connection_string)
        with engine.connect() as conn:
            df.to_sql(table_name, conn, if_exists=if_exists, index=False)
            return True
