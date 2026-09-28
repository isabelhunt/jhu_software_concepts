from sqlalchemy import Column, Date, Float, Identity, Integer, Text, URL, create_engine
from sqlalchemy.orm import declarative_base

if __package__:
    from .db_config import get_db_settings
else:
    from db_config import get_db_settings

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
    """Create a PostgreSQL engine and verify that it can connect.

    Read settings with :func:`get_db_settings`, build a psycopg URL, and print
    a success message. Close the verification connection before returning.

    :returns: The engine after a successful connection check.
    :rtype: sqlalchemy.engine.Engine
    :raises ValueError: Database settings are missing or invalid.
    :raises sqlalchemy.exc.SQLAlchemyError: Engine creation or connection fails.
    """
    settings = get_db_settings()
    url = URL.create(
        "postgresql+psycopg",
        username=settings["db_user"],
        password=settings["db_password"],
        host=settings["db_host"],
        port=settings["db_port"],
        database=settings["db_name"],
    )
    db = create_engine(url)
    with db.connect():
        print("Connection was successful")
    return db
