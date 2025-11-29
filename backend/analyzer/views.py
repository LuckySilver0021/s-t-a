LAST_ANALYZED = []
from rest_framework.decorators import api_view
from rest_framework.response import Response
from analyzer.utils import calculate_priority, detect_circular
from datetime import datetime
@api_view(['POST'])
def analyze_tasks(request):
    tasks = request.data
    if not isinstance(tasks, list):
        return Response({"error": "Expected a list of tasks"}, status=400)

    # default strategy can be provided via query param ?strategy=smart|fastest|impact|deadline
    strategy = request.GET.get('strategy', 'smart')

    def parse_task_dates(t):
        # normalize due_date strings to date objects if needed
        d = t.get('due_date')
        if d and isinstance(d, str):
            try:
                t['due_date'] = datetime.fromisoformat(d).date()
            except Exception:
                t['due_date'] = None
        return t

    tasks = [parse_task_dates(dict(t)) for t in tasks]

    scored_tasks = analyze_and_score(tasks, strategy=strategy)

    # Save for suggest endpoint
    global LAST_ANALYZED
    LAST_ANALYZED = scored_tasks

    return Response(scored_tasks, status=200)


def analyze_and_score(tasks, strategy='smart'):
    # tasks: list of dicts
    task_map = {t.get('title'): t for t in tasks}

    # detect circular dependencies (using titles as ids)
    cycles = detect_circular({t.get('title'): t for t in tasks})

    scored = []
    for t in tasks:
        # normalize fields
        title = t.get('title') or ('Task ' + str(len(scored) + 1))
        est = t.get('estimated_hours') or 1
        importance = t.get('importance') or 5
        deps = t.get('dependencies') or []

        score, breakdown = calculate_priority({
            'title': title,
            'due_date': t.get('due_date'),
            'estimated_hours': est,
            'importance': importance,
            'dependencies': deps,
        }, task_map, strategy=strategy)

        priority = 'Low'
        if score >= 45:
            priority = 'High'
        elif score >= 25:
            priority = 'Medium'

        scored.append({
            'title': title,
            'due_date': t.get('due_date').isoformat() if t.get('due_date') else None,
            'estimated_hours': est,
            'importance': importance,
            'dependencies': deps,
            'score': score,
            'priority': priority,
            'explanation': breakdown.get('notes', []),
            'breakdown': breakdown,
        })

    scored_sorted = sorted(scored, key=lambda x: x['score'], reverse=True)
    return scored_sorted

