"""Compatibility entry point; the application lives in board/."""

if __package__:
    from .run import app
else:
    from run import app


if __name__ == "__main__":
    app.run(host="localhost", port=8080, debug=True)
