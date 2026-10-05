"""This module uses SQL to analyze GradCafe graduate acceptace data """
from psycopg import sql

from db_config import get_db_settings
from load_data import create_connection

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
                LIMIT 1
                """).format(
                table_name = sql.Identifier("applicants"),
                column = sql.Identifier("term"),
                )
        params = {'term' : 'Fall 2026'}
        cursor.execute(statement, params)
        count = cursor.fetchone()
        print(f"Fall 2026 applicant count: {count[0]}")

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
            LIMIT 1
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
            FROM {table_name} WHERE {column} IS NOT NULL
            LIMIT 1
        """
            ).format(
            table_name = sql.Identifier("applicants"),
            column = sql.Identifier("gpa"),
            )
        cursor.execute(statement)
        average_gpa = cursor.fetchone()[0]
        print(f"Average GPA: {average_gpa:.2f}")

    with connection.cursor() as cursor:
        statement = sql.SQL("""SELECT AVG({column})
            FROM {table_name} WHERE {column} IS NOT NULL
            LIMIT 1
        """
            ).format(
            table_name = sql.Identifier("applicants"),
            column = sql.Identifier("gre"),
            )
        cursor.execute(statement)
        average_gre = cursor.fetchone()[0]
        print(f"Average GRE Quantitative: {average_gre:.2f}")

    with connection.cursor() as cursor:
        statement = sql.SQL("""SELECT AVG({column})
            FROM {table_name} WHERE {column} IS NOT NULL
            LIMIT 1
        """
            ).format(
            table_name = sql.Identifier("applicants"),
            column = sql.Identifier("gre_v"),
            )
        cursor.execute(statement)
        average_gre_v = cursor.fetchone()[0]
        print(f"Average GRE Verbal: {average_gre_v:.2f}")

    with connection.cursor() as cursor:
        statement = sql.SQL("""SELECT AVG({column})
            FROM {table_name} WHERE {column} IS NOT NULL
            LIMIT 1
        """
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
        statment = sql.SQL("""
            SELECT AVG({column})
            FROM {table_name}
            WHERE LOWER(TRIM({column_2})) = %(us_or_international)s
              AND {column_3} = %(term)s
              AND {column} IS NOT NULL
            LIMIT 1
        """).format(
            table_name = sql.Identifier("applicants"),
            column = sql.Identifier("gpa"),
            column_2 = sql.Identifier("us_or_international"),
            column_3 = sql.Identifier("term"),
            )
        params = {"us_or_international" : "american" , "term" : "Fall 2026"}
        cursor.execute(statment, params)
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
        statement = sql.SQL("""
            SELECT ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE LOWER(TRIM({column})) = %(status)s
                ) / NULLIF(COUNT(*), 0),
                2
            )
            FROM {table_name}
            WHERE {column_2} = %(term)s
            LIMIT 1
        """).format(
            table_name=sql.Identifier("applicants"),
            column=sql.Identifier("status"),
            column_2=sql.Identifier("term"),
        )
        params = {"status": "accepted", "term": "Fall 2025"}
        cursor.execute(statement, params)
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
        statement = sql.SQL("""
            SELECT AVG({column})
            FROM {table_name}
            WHERE LOWER(TRIM({column_2})) = %(status)s
              AND {column_3} = %(term)s
              AND {column} IS NOT NULL
            LIMIT 1
        """).format(
            table_name=sql.Identifier("applicants"),
            column=sql.Identifier("gpa"),
            column_2=sql.Identifier("status"),
            column_3=sql.Identifier("term"),
        )
        params = {"status": "accepted", "term": "Fall 2026"}
        cursor.execute(statement, params)
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
        statement = sql.SQL("""
            SELECT COUNT(*)
            FROM {table_name}
            WHERE (
                LOWER({column}) LIKE %(university)s
                OR LOWER({column}) LIKE %(abbreviation)s
                OR LOWER({column}) LIKE %(short_name)s
            )
              AND LOWER({column}) LIKE %(program)s
              AND LOWER(TRIM({column_2})) IN (
                  %(masters)s, %(master)s, %(possessive_master)s
              )
            LIMIT 1
        """).format(
            table_name=sql.Identifier("applicants"),
            column=sql.Identifier("program"),
            column_2=sql.Identifier("degree"),
        )
        params = {
            "university": "%johns hopkins university%",
            "abbreviation": "%jhu%",
            "short_name": "%johns hopkins%",
            "program": "%computer science%",
            "masters": "masters",
            "master": "master",
            "possessive_master": "master's",
        }
        cursor.execute(statement, params)
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
        statement = sql.SQL("""
            SELECT COUNT(*)
            FROM {table_name}
            WHERE {column} = %(term)s
              AND LOWER(TRIM({column_2})) = %(status)s
              AND LOWER(TRIM({column_3})) = %(degree)s
              AND LOWER({column_4}) LIKE %(program)s
              AND (
                  LOWER({column_4}) LIKE %(georgetown)s
                  OR LOWER({column_4}) LIKE %(mit_full)s
                  OR LOWER({column_4}) LIKE %(mit)s
                  OR LOWER({column_4}) LIKE %(stanford)s
                  OR LOWER({column_4}) LIKE %(carnegie_mellon)s
              )
            LIMIT 1
        """).format(
            table_name=sql.Identifier("applicants"),
            column=sql.Identifier("term"),
            column_2=sql.Identifier("status"),
            column_3=sql.Identifier("degree"),
            column_4=sql.Identifier("program"),
        )
        params = {
            "term": "Fall 2026",
            "status": "accepted",
            "degree": "phd",
            "program": "%computer science%",
            "georgetown": "%georgetown university%",
            "mit_full": "%massachusetts institute of technology%",
            "mit": "%mit%",
            "stanford": "%stanford university%",
            "carnegie_mellon": "%carnegie mellon university%",
        }
        cursor.execute(statement, params)
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
        statement = sql.SQL("""
            SELECT COUNT(*)
            FROM {table_name}
            WHERE {column} = %(term)s
              AND LOWER(TRIM({column_2})) = %(status)s
              AND LOWER(TRIM({column_3})) = %(degree)s
              AND LOWER({column_4}) LIKE %(program)s
              AND (
                  LOWER({column_5}) LIKE %(georgetown)s
                  OR LOWER({column_5}) LIKE %(mit_full)s
                  OR LOWER({column_5}) LIKE %(mit)s
                  OR LOWER({column_5}) LIKE %(stanford)s
                  OR LOWER({column_5}) LIKE %(carnegie_mellon)s
              )
            LIMIT 1
        """).format(
            table_name=sql.Identifier("applicants"),
            column=sql.Identifier("term"),
            column_2=sql.Identifier("status"),
            column_3=sql.Identifier("degree"),
            column_4=sql.Identifier("llm_generated_program"),
            column_5=sql.Identifier("llm_generated_university"),
        )
        params = {
            "term": "Fall 2026",
            "status": "accepted",
            "degree": "phd",
            "program": "%computer science%",
            "georgetown": "%georgetown university%",
            "mit_full": "%massachusetts institute of technology%",
            "mit": "%mit%",
            "stanford": "%stanford university%",
            "carnegie_mellon": "%carnegie mellon university%",
        }
        cursor.execute(statement, params)
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
        statement = sql.SQL("""
            SELECT ROUND(
                100.0 * COUNT({column}) / NULLIF(COUNT(*), 0),
                2
            )
            FROM {table_name}
            LIMIT 1
        """).format(
            table_name=sql.Identifier("applicants"),
            column=sql.Identifier("gre_v"),
        )
        cursor.execute(statement)
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
        statement = sql.SQL("""
            SELECT COUNT({column})
            FROM {table_name}
            WHERE LOWER({column}) LIKE %(university)s
            LIMIT 1
        """).format(
            table_name=sql.Identifier("applicants"),
            column=sql.Identifier("program"),
        )
        params = {"university": "%temple university%"}
        cursor.execute(statement, params)
        count = cursor.fetchone()
        print(f"Temple University Applicant Count: {count[0]}")

if __name__ == "__main__": # pragma: no cover
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
