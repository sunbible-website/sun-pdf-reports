import pandas as pd

def clean(value):
        return str(value).strip() if pd.notna(value) and str(value).strip() else ""
