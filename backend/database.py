from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

user = "root"
password = "root"
host = "127.0.0.1"
port = 3306
database = "scratchDB"

URL = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"

# FastAPI
engine = create_engine(URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()