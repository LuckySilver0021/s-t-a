# Smart Task Analyzer

Demo app that scores & prioritizes tasks by urgency, importance, effort and dependencies.

Run (development):

1. Create venv and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Start backend:

```bash
python manage.py runserver 8000
```

3. Serve frontend (optional) from project root so it's available at http://localhost:8001:

```bash
python -m http.server 8001
# then open http://localhost:8001/frontend.html
```

API Endpoints

- `POST /api/tasks/analyze/?strategy=smart|fastest|impact|deadline` — accepts JSON array of tasks and returns scored/sorted array.
- `GET /api/tasks/suggest/?strategy=...` — returns top-3 suggestions based on last analyzed set.

Notes

- CORS is enabled for `http://localhost:8001` to allow the demo frontend to call the backend.
- Unit tests for utils and basic integration test for views are included under `analyzer/tests/`.

Next steps: add persistence, unit tests for views with DB persistence, and optional visualizations.