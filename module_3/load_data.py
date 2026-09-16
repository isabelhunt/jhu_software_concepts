import json
from datetime import datetime
from pathlib import Path

import psycopg
from psycopg import OperationalError
from psycopg import sql

# connect to the database 

def create_connection(db_name, db_user, db_password, db_host, db_port):
    connection = None
    try:
        connection = psycopg.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
                )
        print("Connection to PostgreSQL DB successful")
    except OperationalError as e:
        print(f"The error '{e}' occurred")
    return connection

def load_data(connection, table_name="applicants", file_path=None):
    """Append JSON Lines records; PostgreSQL generates each record's p_id.

    The connection should point to grad_data. Repeated calls append the data
    again. All inserts are committed together, or rolled back on failure.
    """
    source = (Path(file_path) if file_path is not None else
              Path(__file__).with_name("llm_extend_applicant_data.json"))
    rows = []
    with source.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                date_added = entry.get("date_added")
                if date_added:
                    date_added = datetime.strptime(date_added, "%b %d, %Y").date()
                else:
                    date_added = None

                scores = [
                    float(entry[key]) if entry.get(key) not in (None, "") else None
                    for key in ("GPA", "GRE", "GRE V", "GRE AW")
                ]
                rows.append((
                    entry.get("program"), entry.get("comments"), date_added,
                    entry.get("url"), entry.get("status"), entry.get("term"),
                    entry.get("US/International"), *scores, entry.get("Degree"),
                    entry.get("llm-generated-program"),
                    entry.get("llm-generated-university"),
                ))
            except (ValueError, TypeError, AttributeError) as error:
                raise ValueError(f"Invalid record on line {line_number}: {error}") from error

    table = sql.Identifier(table_name)
    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute(sql.SQL("""
                CREATE TABLE IF NOT EXISTS {} (
                    p_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    program TEXT,
                    comments TEXT,
                    date_added DATE,
                    url TEXT,
                    status TEXT,
                    term TEXT,
                    us_or_international TEXT,
                    gpa FLOAT,
                    gre FLOAT,
                    gre_v FLOAT,
                    gre_aw FLOAT,
                    degree TEXT,
                    llm_generated_program TEXT,
                    llm_generated_university TEXT
                )
            """).format(table))
            cursor.executemany(sql.SQL("""
                INSERT INTO {} (
                    program, comments, date_added, url, status, term,
                    us_or_international, gpa, gre, gre_v, gre_aw, degree,
                    llm_generated_program, llm_generated_university
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """).format(table), rows)
    return len(rows)

def print_applicants(connection):
    """Print the first 100 applicants ordered by p_id, with column headings."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM applicants ORDER BY p_id LIMIT 100")
        print("\t".join(column.name for column in cursor.description))
        for row in cursor.fetchall():
            print("\t".join("NULL" if value is None else str(value) for value in row))


def _delete(connection, start_id, end_id):
    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM applicants WHERE p_id BETWEEN %s AND %s",
                (start_id, end_id),
            )
            return cursor.rowcount

if __name__ == "__main__":
    connection = create_connection("grad_data", "postgres", "lanie89", "localhost", "54830")
    if connection is not None:
        with connection:
            print_applicants(connection)

"""
    if connection is not None:
        with connection:
            count = load_data(connection)
            print(f"Loaded {count} records into grad_data.")
"""
