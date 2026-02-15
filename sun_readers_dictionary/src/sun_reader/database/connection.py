from sqlalchemy import create_engine
from urllib.parse import quote_plus
from config import Config

def get_engine():
    # URL-encode the password to handle special characters
    password = quote_plus(Config.DB_PASSWORD)

    conn_str = (
        f"postgresql+psycopg2://{Config.DB_USER}:{password}"
        f"@{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}"
    )

    engine = create_engine(conn_str)
    return engine
