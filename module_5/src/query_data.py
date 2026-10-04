"""This module uses SQL to analyze GradCafe graduate acceptace data """
import psycopg
from psycopg import OperationalError, sql

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

# Q1
def fall_26_apps(connection):
    """Count Fall 2026 applications.

    Print the answer to standard output.

    :param connection: Open PostgreSQL connection containing the applicants table.
    :type connection: psycopg.Connection
    :returns: None; answers are printed to standard output.
    :rtype: None
    :raises psycopg.Error: A database query fails.
    """
    with connection.cursor() as cursor:
        statement = sql.SQL(
                """SELECT COUNT({column}) FROM {table_name} 
                WHERE {column} = %(term)s
                """).format(
                table_name = sql.Identifier("applicants"),
                column = sql.Identifier("term"),
                )
        params = {'term' : 'Fall 2026'}
        cursor.execute(statement, params)
        count = cursor.fetchall()
        print(f"Fall 2026 applicant count: {count[0][0]}")

# Q2
def percent_international(connection):
    """Calculate the international percentage among records with reported nationality.

    Print the answer to standard output. Format numeric output to two decimal places.

    :param connection: Open PostgreSQL connection containing the applicants table.
    :type connection: psycopg.Connection
    :returns: None; answers are printed to standard output.
    :rtype: None
    :raises psycopg.Error: A database query fails.
    :raises TypeError: An aggregate is ``None`` and cannot be formatted numerically.
    """
    with connection.cursor() as cursor:
        statement = sql.SQL("""
            SELECT ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE LOWER(TRIM({column})) = %(us_or_international)s
                ) / NULLIF(COUNT(*), 0),
                2
            )
            FROM {table_name}
            WHERE {column} IS NOT NULL
        """).format(
            table_name = sql.Identifier("applicants"),
            column = sql.Identifier("us_or_international"),
        )
        params = {"us_or_international" : "international"}
        cursor.execute(statement, params)
        percentage = cursor.fetchone()[0]
        print(f"Percent International: {percentage:.2f}%")

# Q3
def average_stats (connection):
    """Calculate mean GPA and GRE scores, excluding missing values for each score.

    Print the answer to standard output. Format numeric output to two decimal places.

    :param connection: Open PostgreSQL connection containing the applicants table.
    :type connection: psycopg.Connection
    :returns: None; answers are printed to standard output.
    :rtype: None
    :raises psycopg.Error: A database query fails.
    :raises TypeError: An aggregate is ``None`` and cannot be formatted numerically.
    """
    with connection.cursor() as cursor:
        statement = sql.SQL("""SELECT AVG({column}) 
            FROM {table_name} WHERE {column} IS NOT NULL"""
            ).format(
            table_name = sql.Identifier("applicants"),
            column = sql.Identifier("gpa"),
            )
        cursor.execute(statement)
        average_gpa = cursor.fetchone()[0]
        print(f"Average GPA: {average_gpa:.2f}")

    with connection.cursor() as cursor:
        statement = sql.SQL("""SELECT AVG({column}) 
            FROM {table_name} WHERE {column} IS NOT NULL"""
            ).format(
            table_name = sql.Identifier("applicants"),
            column = sql.Identifier("gre"),
            )
        cursor.execute(statement)
        average_gre = cursor.fetchone()[0]
        print(f"Average GRE Quantitative: {average_gre:.2f}")

    with connection.cursor() as cursor:
        statement = sql.SQL("""SELECT AVG({column}) 
            FROM {table_name} WHERE {column} IS NOT NULL"""
            ).format(
            table_name = sql.Identifier("applicants"),
            column = sql.Identifier("gre_v"),
            )
        cursor.execute(statement)
        average_gre_v = cursor.fetchone()[0]
        print(f"Average GRE Verbal: {average_gre_v:.2f}")

    with connection.cursor() as cursor:
        statement = sql.SQL("""SELECT AVG({column}) 
            FROM {table_name} WHERE {column} IS NOT NULL"""
            ).format(
            table_name = sql.Identifier("applicants"),
            column = sql.Identifier("gre_aw"),
            )
        cursor.execute(statement)
        average_gre_aw = cursor.fetchone()[0]
        print(f"Average GRE Analytical Writing: {average_gre_aw:.2f}")

# Q4
def average_american_fall_26_gpa(connection):
    """Calculate mean GPA for American Fall 2026 applicants.

    Print the answer to standard output. Format numeric output to two decimal places.

    :param connection: Open PostgreSQL connection containing the applicants table.
    :type connection: psycopg.Connection
    :returns: None; answers are printed to standard output.
    :rtype: None
    :raises psycopg.Error: A database query fails.
    :raises TypeError: An aggregate is ``None`` and cannot be formatted numerically.
    """
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT AVG(gpa)
            FROM applicants
            WHERE LOWER(TRIM(us_or_international)) = 'american'
              AND term = 'Fall 2026'
              AND gpa IS NOT NULL
        """)
        average_gpa = cursor.fetchone()[0]
        print(f"Average GPA of American Fall 2026 applicants: {average_gpa:.2f}")

# Q5
def percent_accepted_fall_25(connection):
    """Calculate the acceptance percentage for Fall 2025 applications.

    Print the answer to standard output. Format numeric output to two decimal places.

    :param connection: Open PostgreSQL connection containing the applicants table.
    :type connection: psycopg.Connection
    :returns: None; answers are printed to standard output.
    :rtype: None
    :raises psycopg.Error: A database query fails.
    :raises TypeError: An aggregate is ``None`` and cannot be formatted numerically.
    """
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE LOWER(TRIM(status)) = 'accepted'
                ) / NULLIF(COUNT(*), 0),
                2
            )
            FROM applicants
            WHERE term = 'Fall 2025'
        """)
        percentage = cursor.fetchone()[0]
        print(f"Fall 2025 acceptance percentage: {percentage:.2f}%")

# Q6
def average_accepted_fall_26_gpa(connection):
    """Calculate mean GPA for accepted Fall 2026 applicants.

    Print the answer to standard output. Format numeric output to two decimal places.

    :param connection: Open PostgreSQL connection containing the applicants table.
    :type connection: psycopg.Connection
    :returns: None; answers are printed to standard output.
    :rtype: None
    :raises psycopg.Error: A database query fails.
    :raises TypeError: An aggregate is ``None`` and cannot be formatted numerically.
    """
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT AVG(gpa)
            FROM applicants
            WHERE LOWER(TRIM(status)) = 'accepted'
              AND term = 'Fall 2026'
              AND gpa IS NOT NULL
        """)
        average_gpa = cursor.fetchone()[0]
        print(f"Average GPA of accepted Fall 2026 applicants: {average_gpa:.2f}")

# Q7
def jhu_comp_sci_masters_count(connection):
    """Count Johns Hopkins computer science master's applications.

    Print the answer to standard output.

    :param connection: Open PostgreSQL connection containing the applicants table.
    :type connection: psycopg.Connection
    :returns: None; answers are printed to standard output.
    :rtype: None
    :raises psycopg.Error: A database query fails.
    """
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*)
            FROM applicants
            WHERE (
                LOWER(program) LIKE '%johns hopkins university%'
                OR LOWER(program) LIKE '%jhu%'
                OR LOWER(program) LIKE '%johns hopkins%'
            )
              AND LOWER(program) LIKE '%computer science%'
              AND LOWER(TRIM(degree)) IN ('masters', 'master', 'master''s')
        """)
        count = cursor.fetchone()[0]
        print(f"Johns Hopkins Comp Sci Applicants: {count}")

# Q8
def accepted_fall_26_comp_sci_count(connection):
    """Count accepted Fall 2026 computer science PhD applications using original fields.

    Print the answer to standard output.
    Restrict universities to Georgetown, MIT, Stanford, and Carnegie Mellon.

    :param connection: Open PostgreSQL connection containing the applicants table.
    :type connection: psycopg.Connection
    :returns: The matching application count.
    :rtype: int
    :raises psycopg.Error: A database query fails.
    """
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*)
            FROM applicants
            WHERE term = 'Fall 2026'
              AND LOWER(TRIM(status)) = 'accepted'
              AND LOWER(TRIM(degree)) = 'phd'
              AND LOWER(program) LIKE '%computer science%'
              AND (
                  LOWER(program) LIKE '%georgetown university%'
                  OR LOWER(program) LIKE '%massachusetts institute of technology%'
                  OR LOWER(program) LIKE '%mit%'
                  OR LOWER(program) LIKE '%stanford university%'
                  OR LOWER(program) LIKE '%carnegie mellon university%'
              )
        """)
        count = cursor.fetchone()[0]
        print(f"Original Field Count: {count}")
        return count

# Q9
def accepted_fall_26_llm_comp_sci_count(connection):
    """Count accepted Fall 2026 computer science PhD applications using LLM fields.

    Print the answer to standard output.
    Restrict universities to Georgetown, MIT, Stanford, and Carnegie Mellon.

    :param connection: Open PostgreSQL connection containing the applicants table.
    :type connection: psycopg.Connection
    :returns: The matching application count.
    :rtype: int
    :raises psycopg.Error: A database query fails.
    """
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*)
            FROM applicants
            WHERE term = 'Fall 2026'
              AND LOWER(TRIM(status)) = 'accepted'
              AND LOWER(TRIM(degree)) = 'phd'
              AND LOWER(llm_generated_program) LIKE '%computer science%'
              AND (
                  LOWER(llm_generated_university) LIKE '%georgetown university%'
                  OR LOWER(llm_generated_university) LIKE '%massachusetts institute of technology%'
                  OR LOWER(llm_generated_university) LIKE '%mit%'
                  OR LOWER(llm_generated_university) LIKE '%stanford university%'
                  OR LOWER(llm_generated_university) LIKE '%carnegie mellon university%'
              )
        """)
        count = cursor.fetchone()[0]
        print(f"llm Field Count: {count}")
        return count

#Q10
def percent_reported_gre_v(connection):
    """Calculate the percentage of all applicants reporting a GRE verbal score.

    Print the answer to standard output. Format numeric output to two decimal places.

    :param connection: Open PostgreSQL connection containing the applicants table.
    :type connection: psycopg.Connection
    :returns: None; answers are printed to standard output.
    :rtype: None
    :raises psycopg.Error: A database query fails.
    :raises TypeError: An aggregate is ``None`` and cannot be formatted numerically.
    """
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT ROUND(
                100.0 * COUNT(gre_v) / NULLIF(COUNT(*), 0),
                2
            )
            FROM applicants
            """)
        percentage = cursor.fetchone()[0]
        print(f"Percent reporting GRE verbal: {percentage:.2f}%")

#Q11
def temple_apps(connection):
    """Count applications whose program names Temple University.

    Print the answer to standard output.

    :param connection: Open PostgreSQL connection containing the applicants table.
    :type connection: psycopg.Connection
    :returns: None; answers are printed to standard output.
    :rtype: None
    :raises psycopg.Error: A database query fails.
    """
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(program) 
            FROM applicants
            WHERE lower(program) like '%temple university%'
            """)
        count = cursor.fetchall()
        print(f"Temple University Applicant Count: {count[0][0]}")

if __name__ == "__main__":
    db_connection = create_connection(**get_db_settings())
    if db_connection is not None:
        with db_connection:
            fall_26_apps(db_connection)
            percent_international(db_connection)
            average_stats(db_connection)
            average_american_fall_26_gpa(db_connection)
            percent_accepted_fall_25(db_connection)
            average_accepted_fall_26_gpa(db_connection)
            jhu_comp_sci_masters_count(db_connection)
            original_count = accepted_fall_26_comp_sci_count(db_connection)
            llm_count = accepted_fall_26_llm_comp_sci_count(db_connection)
            print(f"Difference: {original_count - llm_count}")
            percent_reported_gre_v(db_connection)
            temple_apps(db_connection)
