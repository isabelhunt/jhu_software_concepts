import psycopg
from psycopg import OperationalError
from psycopg import sql

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

# Q1
def fall_26_apps(connection):   
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(term) FROM applicants WHERE term = 'Fall 2026'")
        count = cursor.fetchall()
        print(f"Fall 2026 applicant count: {count[0][0]}")

# Q2
def percent_international(connection):   
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE LOWER(TRIM(us_or_international)) = 'international'
                ) / NULLIF(COUNT(*), 0),
                2
            )
            FROM applicants
            WHERE us_or_international IS NOT NULL
        """)
        percentage = cursor.fetchone()[0]
        print(f"Percent International: {percentage:.2f}%")

# Q3
def average_stats (connection):
    with connection.cursor() as cursor:
        cursor.execute("SELECT AVG(gpa) FROM applicants WHERE gpa IS NOT NULL")
        average_gpa = cursor.fetchone()[0]
        print(f"Average GPA: {average_gpa:.2f}")

        cursor.execute("SELECT AVG(gre) FROM applicants WHERE gre IS NOT NULL")
        average_gre = cursor.fetchone()[0]
        print(f"Average GRE Quantitative: {average_gre:.2f}")

        cursor.execute("SELECT AVG(gre_v) FROM applicants WHERE gre_v IS NOT NULL")
        average_gre_v = cursor.fetchone()[0]
        print(f"Average GRE Verbal: {average_gre_v:.2f}")

        cursor.execute("SELECT AVG(gre_aw) FROM applicants WHERE gre_aw IS NOT NULL")
        average_gre_aw = cursor.fetchone()[0]
        print(f"Average GRE Analytical Writing: {average_gre_aw:.2f}")

# Q4
def average_american_fall_26_gpa(connection):
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
        print(f"Percent Fall 2025 acceptances entered: {percentage:.2f}%")

# Q6
def average_accepted_fall_26_gpa(connection):
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
"""
What percentage of students reported a GRE verbal score?
"""
def percent_reported_gre_v(connection):
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
"""
Number of applicants who applied to Temple University 
"""
def temple_apps(connection):   
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(program) 
            FROM applicants
            WHERE lower(program) like '%temple university%'""")
        count = cursor.fetchall()
        print(f"Temple University Applicant Count: {count[0][0]}")


if __name__ == "__main__":
    connection = create_connection("grad_data", "postgres", "lanie89", "localhost", "54830")
    if connection is not None:
        with connection:
            fall_26_apps(connection)
            percent_international(connection)
            average_stats(connection)
            average_american_fall_26_gpa(connection)
            percent_accepted_fall_25(connection)
            average_accepted_fall_26_gpa(connection)
            jhu_comp_sci_masters_count(connection)
            original_count = accepted_fall_26_comp_sci_count(connection)
            llm_count = accepted_fall_26_llm_comp_sci_count(connection)
            print(f"Difference: {original_count - llm_count}")
            percent_reported_gre_v(connection)
            temple_apps(connection)
