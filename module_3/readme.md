Isabel Hunt (ihunt5)
Module 3 Assignment: Database Queries due on September 20th @11:59 pm

### SSH to the github repo ###

git@github.com:isabelhunt/jhu_software_concepts.git

### Database configuration ###

Install dependencies with `python -m pip install -r module_3/requirements.txt`.
For a new checkout, copy `module_3/.env.example` to `module_3/.env` and fill in
`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT` for PostgreSQL.
The app, ORM queries, SQL queries, and loader share these settings. Existing
environment variables take precedence over the file. The local `.env` file
is excluded from Git. 

To load the data into a postgreSQL locally hosted database:
`python load_data.py`

To run the SQL queries:
`python query_data.py`

To run the SQL Alchemy queries:
`python orm_queries.py`

To run the Flask webpage:
`python app.py` 
go to http://localhost:8080/ in any browser 

The flask webpage loads the data that is queried within orm_queries.py,
The Pull Data button runs scrape.py, puts the resulting json through llm_hosting/app, and then load_data.py to update applicants database
The Update Analysis button runs orm_queries.py and refreshes the page 

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
