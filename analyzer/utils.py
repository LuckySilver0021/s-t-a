from datetime import datetime


"""Priority scoring utilities.

Design notes (short & simple):
- Urgency: tasks due sooner (or past-due) should be prioritized because they
    must be addressed immediately to avoid fallout.
- Importance: user-provided 1-10 rating; multiplied to reflect long-term
    impact compared to small quick wins.
- Effort: low estimated hours are "quick wins" and get a small boost.
- Dependencies: tasks that block others get extra weight so unblocking
    increases overall throughput.

We combine these factors with adjustable weights (strategies) so the
behavior can be tuned (fastest wins, high impact, deadline driven, smart).
Edge cases: invalid/missing fields are given sensible defaults and recorded
in breakdown notes; circular dependencies are detected elsewhere before
scoring and will result in a 400 response from the API.
"""


def calculate_priority(task, task_map, strategy='smart', weights_override=None):
    """
    Calculates a priority score for a task based on urgency, importance, effort, and dependencies.
    - Handles missing/invalid fields with defaults and notes.
    - Configurable via strategy or weights_override.
    - Returns a breakdown and human-readable explanation.
    """
    """
    Calculate a priority score and breakdown for a task.
    strategy: 'smart' | 'fastest' | 'impact' | 'deadline'
    Returns (score:int, breakdown:dict)
    """
    notes = []

    # --- Normalize due_date if it's a string ---
    due_date = task.get("due_date")
    if isinstance(due_date, str):
        try:
            due_date = datetime.fromisoformat(due_date).date()
            task['due_date'] = due_date
            notes.append("Parsed due_date string")
        except Exception:
            notes.append("Invalid due_date format; ignored")
            due_date = None

    # --- 1. Urgency ---
    # Rationale: tasks with less time remaining (or past-due) should get
    # a higher urgency_raw so they bubble up. We give a strong boost for
    # past-due and a medium boost for due-today.
    urgency_raw = 0
    if due_date:
        today = datetime.today().date()
        try:
            days_left = (due_date - today).days
        except Exception:
            days_left = None

        if days_left is None:
            urgency_raw = 0
        else:
            if days_left < 0:
                urgency_raw = 30
                notes.append("Past due date")
            elif days_left == 0:
                urgency_raw = 25
                notes.append("Due today")
            else:
                urgency_raw = max(0, 20 - days_left)
                notes.append(f"Urgency days_left={days_left}")

    # --- 2. Importance ---
    # Rationale: Importance reflects long-term impact. We scale it so
    # user input (1-10) has a meaningful influence on the final score.
    importance = task.get("importance", 5)
    try:
        importance_val = int(importance)
    except Exception:
        importance_val = 5
        notes.append("Invalid importance; defaulted to 5")
    importance_raw = importance_val * 2

    # --- 3. Effort (quick wins) ---
    # Rationale: Low-effort tasks are worth prioritizing sometimes because
    # they increase visible progress quickly; effort_raw rewards small jobs.
    hours = task.get("estimated_hours", 1)
    try:
        hours_val = float(hours)
    except Exception:
        hours_val = 1.0
        notes.append("Invalid estimated_hours; defaulted to 1")
    effort_raw = max(0, 10 - hours_val)

    # --- 4. Dependencies ---
    # Rationale: If a task blocks other tasks, finishing it unlocks work for
    # others. We count only dependencies that exist in the provided task map
    # to avoid giving weight to unknown references.
    deps = task.get("dependencies", []) or []
    dependency_raw = sum(3 for d in deps if d in task_map)

    # Strategy explanation
    # Different users or situations prefer different trade-offs.
    # The 'smart' strategy balances urgency, importance, effort and deps.
    # Other strategies shift those weights to emphasize one factor.
    weights = {
        'smart':      {'u': 2, 'i': 3, 'e': 2, 'd': 2},
        'fastest':    {'u': 1, 'i': 1, 'e': 3, 'd': 1},
        'impact':     {'u': 1, 'i': 4, 'e': 1, 'd': 2},
        'deadline':   {'u': 4, 'i': 1, 'e': 1, 'd': 2},
    }

    # allow caller to override weights (partial overrides allowed)
    base = weights.get(strategy, weights['smart'])
    if isinstance(weights_override, dict):
        w = base.copy()
        for k, v in weights_override.items():
            if k in w and isinstance(v, (int, float)):
                w[k] = v
    else:
        w = base

    score = int(
        urgency_raw * w['u']
        + importance_raw * w['i']
        + effort_raw * w['e']
        + dependency_raw * w['d']
    )

    # clamp score to reasonable range
    score = max(0, min(100, score))

    # Human readable explanation
    # We also assemble a concise explanation string so the frontend can show
    # users why a task was chosen (e.g. "urgency=20, importance=16, ...").
    explanation_parts = []
    if urgency_raw:
        explanation_parts.append(f"urgency={urgency_raw}")
    explanation_parts.append(f"importance={importance_raw}")
    explanation_parts.append(f"effort={effort_raw}")
    if dependency_raw:
        explanation_parts.append(f"dependencies={dependency_raw}")

    explanation_str = ", ".join(explanation_parts)

    breakdown = {
        'urgency_raw': urgency_raw,
        'importance_raw': importance_raw,
        'effort_raw': effort_raw,
        'dependency_raw': dependency_raw,
        'weights': w,
        'notes': notes,
        'explanation': explanation_str,
    }

    return score, breakdown


def detect_circular(tasks):
    visited = set()
    stack = set()

    def dfs(task_id):
        if task_id in stack:
            return True

        if task_id in visited:
            return False

        visited.add(task_id)
        stack.add(task_id)

        for dep in tasks.get(task_id, {}).get("dependencies", []):
            if dfs(dep):
                return True

        stack.remove(task_id)
        return False

    for task_id in tasks:
        if dfs(task_id):
            return True

    return False
