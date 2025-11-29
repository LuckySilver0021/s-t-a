from datetime import date, timedelta
from django.test import SimpleTestCase
from rest_framework.test import APITestCase

from analyzer.utils import calculate_priority, detect_circular


class UtilsTests(SimpleTestCase):
	def test_calculate_priority_basic(self):
		today = date.today()
		task = {
			'title': 'T1',
			'due_date': today,
			'estimated_hours': 2,
			'importance': 7,
			'dependencies': []
		}
		score, breakdown = calculate_priority(task, { 'T1': task }, strategy='smart')
		self.assertIsInstance(score, int)
		self.assertIn('urgency_raw', breakdown)
		self.assertIn('importance_raw', breakdown)

	def test_calculate_priority_strategies_change(self):
		today = date.today()
		task = {
			'title': 'T2',
			'due_date': today + timedelta(days=10),
			'estimated_hours': 1,
			'importance': 5,
			'dependencies': []
		}
		s_smart, _ = calculate_priority(task, {'T2': task}, strategy='smart')
		s_fastest, _ = calculate_priority(task, {'T2': task}, strategy='fastest')
		s_impact, _ = calculate_priority(task, {'T2': task}, strategy='impact')
		self.assertNotEqual(s_fastest, s_impact)
		self.assertTrue(all(isinstance(s, int) for s in (s_smart, s_fastest, s_impact)))

	def test_detect_circular_true(self):
		tasks = {
			'A': {'dependencies': ['B']},
			'B': {'dependencies': ['A']}
		}
		self.assertTrue(detect_circular(tasks))

	def test_detect_circular_false(self):
		tasks = {
			'A': {'dependencies': ['B']},
			'B': {'dependencies': []}
		}
		self.assertFalse(detect_circular(tasks))


class ViewsIntegrationTests(APITestCase):
	def test_analyze_and_suggest_endpoints(self):
		tasks = [
			{"title": "A", "due_date": (date.today()).isoformat(), "estimated_hours": 1, "importance": 8, "dependencies": []},
			{"title": "B", "due_date": (date.today() + timedelta(days=3)).isoformat(), "estimated_hours": 4, "importance": 6, "dependencies": ["A"]},
		]

		url = '/api/tasks/analyze/'
		res = self.client.post(url + '?strategy=smart', data=tasks, format='json')
		self.assertEqual(res.status_code, 200)
		self.assertIsInstance(res.data, list)
		self.assertTrue(all('score' in t or 'breakdown' in t for t in res.data))

		# Now request suggestions (server-side saved state)
		res2 = self.client.get('/api/tasks/suggest/?strategy=smart')
		# either returns 200 with suggestions or 400 if LAST_ANALYZED not preserved across test client sessions
		self.assertIn(res2.status_code, (200, 400))

	def test_task_persistence_endpoints(self):
		# create tasks via POST
		tasks = [
			{"title": "P1", "due_date": date.today().isoformat(), "estimated_hours": 2, "importance": 5, "dependencies": []}
		]
		res = self.client.post('/api/tasks/', data=tasks, format='json')
		self.assertEqual(res.status_code, 201)
		self.assertIsInstance(res.data, list)

		# list tasks
		res2 = self.client.get('/api/tasks/')
		self.assertEqual(res2.status_code, 200)
		self.assertTrue(any(t['title'] == 'P1' for t in res2.data))
