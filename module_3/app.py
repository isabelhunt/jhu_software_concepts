from flask import Flask, render_template
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from models import connect_db
import orm_queries

app = Flask(__name__)

@app.route('/')
def index():
    db = None
    try:
        db = connect_db()
        with Session(db) as session:
            results = {
                "q1": orm_queries.fall_26_apps(session),
                "q4": orm_queries.average_american_fall_26_gpa(session),
                "q5": orm_queries.percent_accepted_fall_25(session),
                "q8": orm_queries.accepted_fall_26_comp_sci_count(session),
                "q9": orm_queries.accepted_fall_26_llm_comp_sci_count(session),
                "q10": orm_queries.percent_reported_gre_v(session),
            }
        return render_template("analysis.html", results=results, error=None)
    except SQLAlchemyError:
        app.logger.exception("Unable to load applicant analysis")
        return render_template(
            "analysis.html", results=None,
            error="Applicant data is unavailable. Please try again later.",
        ), 503
    finally:
        if db is not None:
            db.dispose()


if __name__ == "__main__":
    app.run(host="localhost", port=8080, debug=True)
