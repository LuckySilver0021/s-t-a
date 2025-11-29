from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import TaskSerializer
from .utils import calculate_priority, detect_circular
from datetime import datetime
from .models import Task
from rest_framework import status

LAST_ANALYZED = []


class AnalyzeTasks(APIView):
    def post(self, request):
        # strategy may be provided as query param: ?strategy=fastest|impact|deadline|smart
        strategy = request.query_params.get('strategy', 'smart')

        serializer = TaskSerializer(data=request.data, many=True)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        tasks = serializer.validated_data
        task_map = {t["title"]: t for t in tasks}

        # Circular dependency check
        maps_for_check = {t["title"]: t for t in tasks}
        if detect_circular(maps_for_check):
            return Response(
                {"error": "Circular dependencies detected"}, status=400
            )

        # Scoring
        scored_tasks = []
        for task in tasks:
            score, breakdown = calculate_priority(task, task_map, strategy=strategy)
            task["score"] = score
            task["breakdown"] = breakdown
            # human priority label
            if score >= 45:
                task["priority"] = 'High'
            elif score >= 25:
                task["priority"] = 'Medium'
            else:
                task["priority"] = 'Low'

            scored_tasks.append(task)

        scored_tasks = sorted(scored_tasks, key=lambda x: x["score"], reverse=True)

        # save for suggestions
        global LAST_ANALYZED
        LAST_ANALYZED = scored_tasks

        return Response(scored_tasks)


class SuggestTasks(APIView):
    def get(self, request):
        strategy = request.query_params.get('strategy', 'smart')

        if not LAST_ANALYZED:
            return Response({"message": "No analyzed tasks available. POST to /api/tasks/analyze/ first."}, status=400)

        # Re-score with requested strategy (so frontend can switch strategies)
        task_map = {t['title']: t for t in LAST_ANALYZED}

        # detect cycles
        cycles = detect_circular({t['title']: t for t in LAST_ANALYZED})

        recomputed = []
        for t in LAST_ANALYZED:
            score, breakdown = calculate_priority(t, task_map, strategy=strategy)
            priority = 'Low'
            if score >= 45:
                priority = 'High'
            elif score >= 25:
                priority = 'Medium'

            recomputed.append({
                'title': t['title'],
                'score': score,
                'priority': priority,
                'explanation': breakdown.get('notes', []),
                'breakdown': breakdown,
            })

        recomputed = sorted(recomputed, key=lambda x: x['score'], reverse=True)
        top3 = recomputed[:3]

        return Response({'suggestions': top3, 'cycles': cycles})


class TaskListCreate(APIView):
    """List persisted tasks or create new tasks in DB.

    GET /api/tasks/        -> list persisted tasks
    POST /api/tasks/       -> create tasks (accepts single task object or array)
    """
    def get(self, request):
        tasks = Task.objects.all().order_by('-created_at')
        return Response([t.to_dict() for t in tasks])

    def post(self, request):
        data = request.data
        # accept either single object or array
        items = data if isinstance(data, list) else [data]
        serializer = TaskSerializer(data=items, many=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        created = []
        for obj in serializer.validated_data:
            task_obj, _ = Task.objects.update_or_create(
                title=obj.get('title'),
                defaults={
                    'due_date': obj.get('due_date'),
                    'estimated_hours': obj.get('estimated_hours'),
                    'importance': obj.get('importance'),
                    'dependencies': obj.get('dependencies') or [],
                }
            )
            created.append(task_obj.to_dict())

        return Response(created, status=status.HTTP_201_CREATED)
