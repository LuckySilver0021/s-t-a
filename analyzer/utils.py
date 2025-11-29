from datetime import datetime

def calculate_priority(task, task_map, strategy='smart'):
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
    importance = task.get("importance", 5)
    try:
        importance_val = int(importance)
    except Exception:
        importance_val = 5
        notes.append("Invalid importance; defaulted to 5")
    importance_raw = importance_val * 2

    # --- 3. Effort (quick wins) ---
    hours = task.get("estimated_hours", 1)
    try:
        hours_val = float(hours)
    except Exception:
        hours_val = 1.0
        notes.append("Invalid estimated_hours; defaulted to 1")
    effort_raw = max(0, 10 - hours_val)

    # --- 4. Dependencies ---
    deps = task.get("dependencies", []) or []
    # only count deps that are present in task_map (blocking)
    dependency_raw = sum(3 for d in deps if d in task_map)

    # Strategy weights
    weights = {
        'smart':      {'u': 2, 'i': 3, 'e': 2, 'd': 2},
        'fastest':    {'u': 1, 'i': 1, 'e': 3, 'd': 1},
        'impact':     {'u': 1, 'i': 4, 'e': 1, 'd': 2},
        'deadline':   {'u': 4, 'i': 1, 'e': 1, 'd': 2},
    }

    w = weights.get(strategy, weights['smart'])

    score = int(
        urgency_raw * w['u']
        + importance_raw * w['i']
        + effort_raw * w['e']
        + dependency_raw * w['d']
    )

    # clamp score to reasonable range
    score = max(0, min(100, score))

    breakdown = {
        'urgency_raw': urgency_raw,
        'importance_raw': importance_raw,
        'effort_raw': effort_raw,
        'dependency_raw': dependency_raw,
        'weights': w,
        'notes': notes,
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
