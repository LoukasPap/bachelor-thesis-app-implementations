from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

engine = create_engine("postgresql://postgres:1234567890@localhost/fastapi",
    echo=True,
)

Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)
insp = inspect(engine)