from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()
db_pass = os.getenv("SCRATCH_DB_PASSWORD")
db_user = os.getenv("SCRATCH_DB_USER")
db_name = os.getenv("SCRATCH_DB_NAME")

user = db_user
password = db_pass
host = "127.0.0.1"
port = 3306
database = db_name

URL = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"

# FastAPI
engine = create_engine(URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()