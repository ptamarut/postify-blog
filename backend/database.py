from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Putanja do SQLite baze (blog.db u root folderu projekta)
DB_FILE = os.path.join(os.path.dirname(__file__), "..", "blog.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_FILE}"

# Konekcija prema SQLite bazi
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base klasa za modele
Base = declarative_base()

# Kreiraj tablice ako ne postoje
def init_db():
    from backend.models import Post, User
    Base.metadata.create_all(bind=engine, checkfirst=True)
