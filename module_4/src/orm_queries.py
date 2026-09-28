from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import sessionmaker
if __package__:
    from .models import applicant, connect_db
else:
    from models import applicant, connect_db


# Q1
def fall_26_apps(session):
    """Count Fall 2026 applications.

    Print the answer to standard output.

    :param session: Session used to query applicant records.
    :type session: sqlalchemy.orm.Session
    :returns: The matching application count.
    :rtype: int
    :raises sqlalchemy.exc.SQLAlchemyError: The database query fails.
    """
    count = session.scalar(
        select(func.count(applicant.term)).where(applicant.term == "Fall 2026")
    )
    print(f"Fall 2026 applicant count: {count}")
    return count


# Q4
def average_american_fall_26_gpa(session):
    """Calculate mean GPA for American Fall 2026 applicants.

    Print the answer to standard output. Format numeric output to two decimal places.
    Print ``N/A`` when the aggregate is unavailable.

    :param session: Session used to query applicant records.
    :type session: sqlalchemy.orm.Session
    :returns: The calculated value, or ``None`` when no qualifying data exists.
    :rtype: float or decimal.Decimal or None
    :raises sqlalchemy.exc.SQLAlchemyError: The database query fails.
    """
    average_gpa = session.scalar(
        select(func.avg(applicant.gpa)).where(
            func.lower(func.trim(applicant.us_or_international)) == "american",
            applicant.term == "Fall 2026",
            applicant.gpa.is_not(None),
        )
    )
    result = "N/A" if average_gpa is None else f"{average_gpa:.2f}"
    print(f"Average GPA of American Fall 2026 applicants: {result}")
    return average_gpa


# Q5
def percent_accepted_fall_25(session):
    """Calculate the acceptance percentage for Fall 2025 applications.

    Print the answer to standard output. Format numeric output to two decimal places.
    Print ``N/A`` when the aggregate is unavailable.

    :param session: Session used to query applicant records.
    :type session: sqlalchemy.orm.Session
    :returns: The calculated value, or ``None`` when no qualifying data exists.
    :rtype: float or decimal.Decimal or None
    :raises sqlalchemy.exc.SQLAlchemyError: The database query fails.
    """
    accepted = func.count().filter(func.lower(func.trim(applicant.status)) == "accepted")
    percentage = session.scalar(
        select(func.round(
            Decimal("100.0") * accepted / func.nullif(func.count(), 0), 2
        )).select_from(applicant).where(applicant.term == "Fall 2025")
    )
    result = "N/A" if percentage is None else f"{percentage:.2f}%"
    print(f"Fall 2025 acceptance percentage: {result}")
    return percentage


def _selected_university(column):
    """Build a case-insensitive filter for the selected universities.

    :param column: SQLAlchemy text column containing a program or university name.
    :type column: sqlalchemy.sql.expression.ColumnElement
    :returns: An OR expression matching Georgetown, MIT, Stanford, or Carnegie Mellon.
    :rtype: sqlalchemy.sql.elements.BooleanClauseList
    """
    return or_(
        *(func.lower(column).like(f"%{name}%") for name in (
            "georgetown university",
            "massachusetts institute of technology",
            "mit",
            "stanford university",
            "carnegie mellon university",
        ))
    )


# Q8
def accepted_fall_26_comp_sci_count(session):
    """Count accepted Fall 2026 computer science PhD applications using original fields.

    Print the answer to standard output.
    Restrict universities to Georgetown, MIT, Stanford, and Carnegie Mellon.

    :param session: Session used to query applicant records.
    :type session: sqlalchemy.orm.Session
    :returns: The matching application count.
    :rtype: int
    :raises sqlalchemy.exc.SQLAlchemyError: The database query fails.
    """
    count = session.scalar(
        select(func.count()).select_from(applicant).where(
            applicant.term == "Fall 2026",
            func.lower(func.trim(applicant.status)) == "accepted",
            func.lower(func.trim(applicant.degree)) == "phd",
            func.lower(applicant.program).like("%computer science%"),
            _selected_university(applicant.program),
        )
    )
    print(f"Original Field Count: {count}")
    return count


# Q9
def accepted_fall_26_llm_comp_sci_count(session):
    """Count accepted Fall 2026 computer science PhD applications using LLM fields.

    Print the answer to standard output.
    Restrict universities to Georgetown, MIT, Stanford, and Carnegie Mellon.

    :param session: Session used to query applicant records.
    :type session: sqlalchemy.orm.Session
    :returns: The matching application count.
    :rtype: int
    :raises sqlalchemy.exc.SQLAlchemyError: The database query fails.
    """
    count = session.scalar(
        select(func.count()).select_from(applicant).where(
            applicant.term == "Fall 2026",
            func.lower(func.trim(applicant.status)) == "accepted",
            func.lower(func.trim(applicant.degree)) == "phd",
            func.lower(applicant.llm_generated_program).like("%computer science%"),
            _selected_university(applicant.llm_generated_university),
        )
    )
    print(f"llm Field Count: {count}")
    return count


# Q10
def percent_reported_gre_v(session):
    """Calculate the percentage of all applicants reporting a GRE verbal score.

    Print the answer to standard output. Format numeric output to two decimal places.
    Print ``N/A`` when the aggregate is unavailable.

    :param session: Session used to query applicant records.
    :type session: sqlalchemy.orm.Session
    :returns: The calculated value, or ``None`` when no qualifying data exists.
    :rtype: float or decimal.Decimal or None
    :raises sqlalchemy.exc.SQLAlchemyError: The database query fails.
    """
    percentage = session.scalar(
        select(func.round(
            Decimal("100.0") * func.count(applicant.gre_v)
            / func.nullif(func.count(), 0), 2
        )).select_from(applicant)
    )
    result = "N/A" if percentage is None else f"{percentage:.2f}%"
    print(f"Percent reporting GRE verbal: {result}")
    return percentage


""" 
# Uncomment to run file directly 
if __name__ == "__main__":
    db=connect_db() #establish connection
    Session = sessionmaker(bind=db)
    with Session() as session:
        fall_26_apps(session)
        average_american_fall_26_gpa(session)
        percent_accepted_fall_25(session)
        original_count = accepted_fall_26_comp_sci_count(session)
        llm_count = accepted_fall_26_llm_comp_sci_count(session)
        print(f"Difference: {original_count - llm_count}")
        percent_reported_gre_v(session)
"""
