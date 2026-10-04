import fcntl
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from flask import Blueprint, current_app, jsonify, render_template, request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
if __package__ == "board":
    from models import Applicant
    import orm_queries
else:
    from ..models import Applicant
    from .. import orm_queries

bp = Blueprint("pages", __name__)
MODULE_DIR = Path(__file__).resolve().parents[1]


@bp.post('/pull-data')
def pull_data():
    # A file lock also prevents overlapping jobs in different Flask workers.
    # Keep the file in place: unlinking it would allow competing locks.
    with (MODULE_DIR / '.pull_data.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return jsonify(error="A data pull is already running. Please wait."), 409
        try:
            def run_script(script, *arguments):
                subprocess.run(
                    [sys.executable, str(script), *map(str, arguments)],
                    cwd=script.parent, check=True,
                    # Keep the lock held if the server stops while a child runs.
                    pass_fds=(lock.fileno(),),
                )

            run_script(MODULE_DIR / 'scrape.py')
            output = MODULE_DIR / 'llm_extend_applicant_data.json'
            # Preserve the existing output if enrichment fails partway through.
            with TemporaryDirectory(prefix='.llm-output-', dir=MODULE_DIR) as temporary:
                staged_output = Path(temporary) / output.name
                run_script(
                    MODULE_DIR / 'llm_hosting' / 'app.py',
                    '--file', MODULE_DIR / 'applicant_data.json',
                    '--out', staged_output,
                )
                staged_output.replace(output)
            run_script(MODULE_DIR / 'load_data.py', '--file-path', output)
        except (subprocess.CalledProcessError, OSError):
            current_app.logger.exception("Data pull failed")
            return jsonify(error="The data pull failed. Please try again."), 500
    return jsonify(success=True)

def pull_is_running():
    with (MODULE_DIR / '.pull_data.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
    return False


@bp.get('/update-analysis', endpoint='update_analysis')
@bp.route('/')
def home():
    if request.endpoint == 'pages.update_analysis' and pull_is_running():
        return jsonify(error=(
            "New data is currently being retrieved. Your current analysis is still displayed. "
            "Please update again after Pull Data finishes."
        )), 409
    db = None
    try:
        db = Applicant.connect_db()
        with Session(db) as session:
            results = {
                "q1": orm_queries.fall_26_apps(session),
                "q4": orm_queries.average_american_fall_26_gpa(session),
                "q5": orm_queries.percent_accepted_fall_25(session),
                "q8": orm_queries.accepted_fall_26_comp_sci_count(session),
                "q9": orm_queries.accepted_fall_26_llm_comp_sci_count(session),
                "q10": orm_queries.percent_reported_gre_v(session),
            }
        return render_template("pages/home.html", results=results, error=None)
    except SQLAlchemyError:
        current_app.logger.exception("Unable to load applicant analysis")
        return render_template(
            "pages/home.html", results=None,
            error="Applicant data is unavailable. Please try again later.",
        ), 503
    finally:
        if db is not None:
            db.dispose()

