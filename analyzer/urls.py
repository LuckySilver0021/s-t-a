from django.urls import path
from .views import AnalyzeTasks, SuggestTasks
from .views import TaskListCreate

urlpatterns = [
    path('analyze/', AnalyzeTasks.as_view()),
    path('suggest/', SuggestTasks.as_view()),
    path('', TaskListCreate.as_view()),
]
