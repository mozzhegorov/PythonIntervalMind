from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# engine = create_engine(
#     "postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/pythonmind",
# )
engine = create_engine("sqlite:///db/database.db")
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()
