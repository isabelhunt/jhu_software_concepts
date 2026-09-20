from sqlalchemy import Column, Date, Float, Identity, Integer, Text, URL, create_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class applicant(Base):
    __tablename__ = "applicants"

    p_id = Column(Integer, Identity(always=True), primary_key=True)
    program = Column(Text)
    comments = Column(Text)
    date_added = Column(Date)
    url = Column(Text)
    status = Column(Text)
    term = Column(Text)
    us_or_international = Column(Text)
    gpa = Column(Float)
    gre = Column(Float)
    gre_v = Column(Float)
    gre_aw = Column(Float)
    degree = Column(Text)
    llm_generated_program = Column(Text)
    llm_generated_university = Column(Text)


def connect_db():
    url = URL.create(
        "postgresql+psycopg",
        username="postgres",
        password="lanie89",
        host="localhost",
        port=54830,
        database="grad_data",
    )
    db = create_engine(url)
    with db.connect():
        print("Connection was successful")
    return db
