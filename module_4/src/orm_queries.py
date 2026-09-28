from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import sessionmaker
if __package__:
    from .models import applicant, connect_db
else:
    from models import applicant, connect_db


# Q1
def fall_26_apps(session):
    count = session.scalar(
        select(func.count(applicant.term)).where(applicant.term == "Fall 2026")
    )
    print(f"Fall 2026 applicant count: {count}")
    return count


# Q4
def average_american_fall_26_gpa(session):
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
