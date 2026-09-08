## Running the website
git@github.com:isabelhunt/jhu_software_concepts.git
From the Module 1 folder, run `python run.py` (may need to run python3 run.py depending on env), then open `http://localhost:8080` in your browser.

## Adding a profile photo

Place your photo at `/board/static/images/profile.jpg`. The Home page
will display it as a circular profile image. To use a different filename, update
the `src` value in `/board/templates/pages/home.html`.

## Adding a custom cursor

Place a PNG cursor image at `/board/static/images/cursor.png`. The
website uses the browser-compatible 32×32 version, `cursor-32.png`, with the
standard cursor as a fallback. If you replace `cursor.png`, resize the new file
to 32×32 and save it as `cursor-32.png`.
