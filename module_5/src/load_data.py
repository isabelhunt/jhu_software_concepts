"""This module is used to load the PostgresSQL database

This module houses functions that are used in other modules
to connect to a database and load the database with GradeCafe 
data"""

import argparse
import json
from datetime import datetime
from pathlib import Path

import psycopg
from psycopg import OperationalError
from psycopg import sql

from db_config import get_db_settings

def create_connection(db_name, db_user, db_password, db_host, db_port):
    """Open a PostgreSQL connection and print its connection status.

    Operational errors are printed and handled without being re-raised.

    :param str db_name: PostgreSQL database name.
    :param str db_user: Database login name.
    :param str db_password: Database login password.
    :param str db_host: Database server hostname or address.
    :param int db_port: Database server port.
    :returns: An open connection, or ``None`` if an operational error occurs.
    :rtype: psycopg.Connection or None
    """
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

def read_applicant_rows(file_path=None):
    """Read and normalize applicant records for database insertion.

    :param file_path: JSON or JSON Lines path, or the default output file.
    :type file_path: str or pathlib.Path or None
    :returns: Records as tuples in database column order.
    :rtype: list[tuple]
    :raises ValueError: Input JSON or record fields cannot be parsed.
    :raises OSError: The input file cannot be read.
    """
    source = (Path(file_path) if file_path is not None else
              Path(__file__).with_name("llm_extend_applicant_data.json"))
    rows = []
    with source.open(encoding="utf-8") as file:
        content = file.read()
        records = json.loads(content) if content.lstrip().startswith("[") else content.splitlines()
        for line_number, line in enumerate(records, start=1):
            if isinstance(line, str) and not line.strip():
                continue
            try:
                entry = json.loads(line) if isinstance(line, str) else line
                date_added = entry.get("date_added")
                if date_added:
                    date_added = datetime.strptime(date_added, "%b %d, %Y").date()
                else:
                    date_added = None

                scores = [
                    float(entry[key]) if entry.get(key) not in (None, "") else None
                    for key in ("GPA", "GRE", "GRE V", "GRE AW")
                ]
                program = ", ".join(
                    value.strip()
                    for value in (entry.get("university"), entry.get("program"))
                    if value and value.strip()
                ) or None
                rows.append((
                    program, entry.get("comments"), date_added,
                    entry.get("url"), entry.get("status"), entry.get("term"),
                    entry.get("US/International"), *scores, entry.get("Degree"),
                    entry.get("llm-generated-program"),
                    entry.get("llm-generated-university"),
                ))
            except (ValueError, TypeError, AttributeError) as error:
                raise ValueError(f"Invalid record on line {line_number}: {error}") from error
    return rows


def select_new_rows(rows, existing_rows):
    """Filter duplicates against stored records and within the input batch.

    Records with URLs are compared by URL. Others use all stored fields.

    :param rows: Candidate records in database column order.
    :type rows: list[tuple]
    :param existing_rows: Iterable of records already in the database.
    :type existing_rows: collections.abc.Iterable[tuple]
    :returns: Unique records to insert, preserving input order.
    :rtype: list[tuple]
    """
    seen_urls = set()
    seen_without_url = set()
    for existing in existing_rows:
        if existing[3]:
            seen_urls.add(existing[3])
        else:
            seen_without_url.add(tuple(existing))

    new_rows = []
    for row in rows:
        url = row[3]
        if url:
            if url in seen_urls:
                continue
            seen_urls.add(url)
        else:
            if row in seen_without_url:
                continue
            seen_without_url.add(row)
        new_rows.append(row)
    return new_rows


def load_data(connection, table_name="applicants", file_path=None):
    """Insert new applicant records from a JSON array or JSON Lines file.

    Combine university and program names and convert dates and numeric scores.
    Skip records with an existing URL; records without URLs are deduplicated by
    their complete stored values. Perform database changes in one transaction.

    :param connection: Open PostgreSQL connection used for the transaction.
    :type connection: psycopg.Connection
    :param str table_name: Destination table name; defaults to ``applicants``.
    :param file_path: Input path, or ``None`` for the module's enrichment output file.
    :type file_path: str or pathlib.Path or None
    :returns: Number of newly inserted records.
    :rtype: int
    :raises ValueError: Input JSON or record fields cannot be parsed.
    :raises OSError: The input file cannot be read.
    :raises psycopg.Error: Table creation, locking, or insertion fails.
    """
    rows = read_applicant_rows(file_path)
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
            # Serialize loaders so they cannot insert the same new URL together.
            cursor.execute(sql.SQL("LOCK TABLE {} IN SHARE ROW EXCLUSIVE MODE").format(table))
            cursor.execute(sql.SQL("""
                SELECT program, comments, date_added, url, status, term,
                       us_or_international, gpa, gre, gre_v, gre_aw, degree,
                       llm_generated_program, llm_generated_university
                FROM {}
            """).format(table))
            new_rows = select_new_rows(rows, cursor)

            cursor.executemany(sql.SQL("""
                INSERT INTO {} (
                    program, comments, date_added, url, status, term,
                    us_or_international, gpa, gre, gre_v, gre_aw, degree,
                    llm_generated_program, llm_generated_university
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """).format(table), new_rows)
    return len(new_rows)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load applicant records into PostgreSQL.")
    parser.add_argument("--file-path", type=Path, help="JSON array or JSON Lines input file")
    args = parser.parse_args()
    conn = create_connection(**get_db_settings())
    if conn is None:
        raise SystemExit(1)
    with conn:
        count = load_data(conn, file_path=args.file_path)
        print(f"Loaded {count} records into grad_data.")
