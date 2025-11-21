````markdown name=README.md
```markdown
# Bank Analysis - Web UI (Flask)

This PR adds a small Flask-based web UI scaffold to convert the CLI analysis into a browser-based UI using Flask and simple HTML templates.

Quick start:
1. Create a virtualenv and activate it.
2. pip install -r requirements.txt
3. export FLASK_APP=app.py
4. flask run
5. Open http://127.0.0.1:5000 in your browser.

How to integrate with your existing code:
- Move the core analysis logic from the CLI script into analysis.py and export a function analyze_dataframe(df) (see analysis.py).
- Update the Flask app to import and use analyze_dataframe.
- If the CLI currently reads files directly, refactor file-reading to a small adapter that produces a pandas.DataFrame. The web UI will call the same analysis routine.
```