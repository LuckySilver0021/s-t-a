
# Smart Task Analyzer

## Overview
Smart Task Analyzer is a Django + HTML/JS mini-app that scores and prioritizes tasks based on urgency, importance, effort, and dependencies. It helps users decide what to work on next, with a clean UI and configurable algorithm.

## Setup Instructions
1. Clone the repo and create a virtual environment:
	```bash
	python -m venv .venv
	.venv\Scripts\activate
	pip install -r requirements.txt
	```
2. Run migrations and start the backend:
	```bash
	python manage.py makemigrations
	python manage.py migrate
	python manage.py runserver 8000
	```
3. Serve the frontend (optional, for CORS):
	```bash
	python -m http.server 8001
	# open http://localhost:8001/frontend.html
	```

## API Endpoints
- `POST /api/tasks/analyze/?strategy=smart|fastest|impact|deadline` — accepts JSON array or `{tasks: [...], strategy, weights}` and returns scored/sorted array.
- `GET /api/tasks/suggest/?strategy=...` — returns top-3 suggestions with explanations.
- `GET/POST /api/tasks/` — persist and list tasks.

## Algorithm Explanation
The scoring algorithm combines four factors:
- **Urgency**: Tasks due soon (or past-due) gets higher score.
- **Importance**: User-provided rating (1-10) is scaled accordingly.
- **Effort**: Lower estimated hours are "quick wins" and get a small boost.
- **Dependencies**: Tasks that block others get extra weight, so unblocking increases overall thruput.

Each factor is multiplied by a configurable weight. Four strategies are available:
- `smart`: balanced weights for all factors
- `fastest`: prioritizes quick wins
- `impact`: prioritizes importance
- `deadline`: prioritizes urgency

The algorithm is robust to missing/invalid data. Circular dependencies are detected and rejected. The backend returns a breakdown and a human-readable explanation for each score.

**Example:**
For a task due today, with high importance and low effort, the score will be high due to urgency and importance. If it blocks other tasks, the dependency weight increases its score further.

## Design Decisions
- **Title-based dependencies**: Used Task titles for dependencies & simplicity
- **Configurable weights**: Allows users to tune the algorithm for their tasks (e.g., deadline-driven vs. high-impact).
- **Edge-case handling**: Defaults and notes for missing/invalid fields; circular detection before scoring.
- **No authentication**: Kept simple per assignment.


## Bonus Challenges
- Persistence: Tasks are saved in SQLite via Django model.
- Configurable algorithm: Weights and strategies can be set per request.
- Circular dependency detection: Implemented and tested.


## Unit Tests
At least 3 unit tests for scoring and circular detection are in `analyzer/tests.py`.

## Requirements
- Python 3.8+
- Django 4.0+
- SQLite (default)
- No authentication required

## Sample data (for `/api/tasks/suggest` or `http://127.0.0.1:8000/api/tasks/analyze`)
[
  {
    "id": "task1",
    "title": "Build API",
    "description": "Design and create REST API",
    "deadline": "2025-02-01",
    "priority": 1,
    "category": "Development",
    "dependencies": []
  },
  {
    "id": "task2",
    "title": "Write Documentation",
    "description": "Document endpoints",
    "deadline": "2025-02-10",
    "priority": 2,
    "category": "Documentation",
    "dependencies": ["task1"]
  },
  {
    "id": "task3",
    "title": "Frontend Integration",
    "description": "Connect API to frontend",
    "deadline": "2025-02-05",
    "priority": 1,
    "category": "Integration",
    "dependencies": ["task1"]
  }
]

## Sample data (for `http://127.0.0.1:8001/frontend.html`)
 [
  {"title":"Fix login bug","due_date":"2025-12-01","estimated_hours":3,"importance":8,"dependencies":[]},
  {"title":"Write API docs","due_date":"2025-12-03","estimated_hours":1,"importance":6,"dependencies":["Fix login bug"]},
  {"title":"Quick docs","due_date":"2025-12-02","estimated_hours":1,"importance":4,"dependencies":[]}
]
