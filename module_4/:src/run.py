"""Run the applicant analysis website locally."""

if __package__:
    from .board import create_app
else:
    from board import create_app

app = create_app()


if __name__ == "__main__":
    app.run(host="localhost", port=8080, debug=True)
