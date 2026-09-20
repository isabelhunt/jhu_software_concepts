Isabel Hunt (ihunt5)
Module 2 Assignment: Web Scraping due on September 13th @11:59 pm

### SSH to the github repo ###
git@github.com:isabelhunt/jhu_software_concepts.git


### Part 7: Compare SQL and SQLAlchemy ###

SQL:
cursor.execute("""
    SELECT AVG(gpa)
    FROM applicants
    WHERE LOWER(TRIM(us_or_international)) = 'american'
        AND term = 'Fall 2026'
        AND gpa IS NOT NULL
""")

SQLAlchemy:
select(func.avg(applicant.gpa)).where(
    func.lower(func.trim(applicant.us_or_international)) == "american",
    applicant.term == "Fall 2026",
    applicant.gpa.is_not(None),)

Both SQL and SQLAlchemy can be used to answer the question of "What is the average GPA of American Fall 2026 applicants", and while the result is the same, the approach differs. SQLAlchemy does the same query, but is properly formatted in less lines, which is not necessarily better but has better white space which can improve readability. On the other hand SQL uses key words like "SELECT", "FROM", and "WHERE" which make it extremely easy to read. However, if one has ever coded before, the SQLAlchemy, in my opinion, is also clear and more pythonic. 

