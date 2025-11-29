from django.db import models
import json


class Task(models.Model):
	title = models.CharField(max_length=255, unique=True)
	due_date = models.DateField(null=True, blank=True)
	estimated_hours = models.FloatField(null=True, blank=True)
	importance = models.IntegerField(null=True, blank=True)
	# store dependencies as JSON array of titles
	dependencies = models.JSONField(default=list, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def to_dict(self):
		return {
			'title': self.title,
			'due_date': self.due_date.isoformat() if self.due_date else None,
			'estimated_hours': self.estimated_hours,
			'importance': self.importance,
			'dependencies': self.dependencies,
		}

	def __str__(self):
		return self.title
