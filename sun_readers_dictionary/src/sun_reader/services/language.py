from database.queries import LANGUAGE_QUERY
import pandas as pd

def get_language_name(engine, language_id):
    query = LANGUAGE_QUERY
    
    df = pd.read_sql_query(query, engine, params={"language_id": language_id})

    if df.empty:
        raise ValueError(f"No language found for language_id={language_id}")

    return df.iloc[0]["name"], df.iloc[0]["language_abvr"]
