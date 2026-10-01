"""Define the applicant ORM model and PostgreSQL engine connection helper."""

from datetime import date

from sqlalchemy import Column, Date, Float, Identity, Integer, Text, URL, create_engine
from sqlalchemy.orm import declarative_base

from db_config import get_db_settings


Base = declarative_base()

class Applicant(Base):
    """Map a graduate application result to the ``applicants`` table.

    Mapped fields can be supplied as keyword arguments when creating an
    instance. Fields other than the primary key allow ``None``.

    :ivar int p_id: Database-generated primary key.
    :ivar str program: Combined university and program names.
    :ivar str comments: Applicant's comments about the result.
    :ivar date_added: Date the result was added.
    :vartype date_added: datetime.date
    :ivar str url: Source URL identifying the result.
    :ivar str status: Application decision status.
    :ivar str term: Application term, such as Fall 2026.
    :ivar str us_or_international: Applicant origin category.
    :ivar float gpa: Reported grade point average.
    :ivar float gre: Reported GRE general score.
    :ivar float gre_v: Reported GRE verbal score.
    :ivar float gre_aw: Reported GRE analytical writing score.
    :ivar str degree: Degree sought by the applicant.
    :ivar str llm_generated_program: Program name produced by LLM enrichment.
    :ivar str llm_generated_university: University name from LLM enrichment.
    """

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

    def to_dict(self):
        """Return mapped column values as a dictionary.

        Convert dates to ISO-formatted strings and preserve ``None`` values.
        SQLAlchemy's internal instance state is excluded.

        :returns: Column names mapped to their values, with dates as strings.
        :rtype: dict[str, object]
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            result[column.name] = (
                value.isoformat() if isinstance(value, date) else value
            )
        return result

    @staticmethod
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
