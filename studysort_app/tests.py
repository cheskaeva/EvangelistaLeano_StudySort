from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import StudyTask


class StudyTaskModelTests(TestCase):

    def setUp(self):
        self.future_time = timezone.now() + timezone.timedelta(hours=5)

    def create_task(self, **kwargs):
        data = {
            'task_name': 'Task A',
            'class_name': 'Math',
            'duration': 30,
            'deadline': self.future_time,
            'importance': 3,
            'difficulty': 2
        }
        data.update(kwargs)
        return StudyTask.objects.create(**data)

    def test_string_representation(self):
        task = self.create_task(task_name="Sample Task")
        self.assertEqual(str(task), "Sample Task")

    def test_urgency_factor(self):
        task = self.create_task()
        self.assertIn(task.urgency_factor, [1, 2, 3, 4, 5])

    def test_duration_factor(self):
        task = self.create_task(duration=45)
        self.assertEqual(task.duration_factor, 4)

    def test_priority_score_calculation(self):
        task = self.create_task(duration=30, importance=5, difficulty=5)
        expected = (5*2) + (5*3) + task.duration_factor + (task.urgency_factor*4)
        self.assertEqual(task.priority_score, expected)

    def test_deadline_cannot_be_past(self):
        past_deadline = timezone.now() - timezone.timedelta(hours=1)
        task = StudyTask(
            task_name="Past",
            class_name="Science",
            duration=20,
            deadline=past_deadline,
            importance=3,
            difficulty=2
        )
        with self.assertRaises(ValidationError):
            task.full_clean()

    def test_unique_together(self):
        """Ensure duplicate task_name + class_name is not allowed."""
        self.create_task(task_name="Exam 1", class_name="Math")

        duplicate = StudyTask(
            task_name="Exam 1",
            class_name="Math",
            duration=40,
            deadline=self.future_time,
            importance=4,
            difficulty=3
        )
        with self.assertRaises(ValidationError):
            duplicate.full_clean()


class StudyTaskViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.future = timezone.now() + timezone.timedelta(hours=4)

        # Create initial task
        self.task = StudyTask.objects.create(
            task_name="Test Task",
            class_name="Math",
            duration=30,
            deadline=self.future,
            importance=3,
            difficulty=2
        )

    def test_index_page_loads(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Task")

    def test_add_task(self):
        url = reverse("add_task")
        data = {
            "task_name": "New Task",
            "class_name": "Math",
            "duration": 45,
            "deadline": (timezone.now() + timezone.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            "importance": 3,
            "difficulty": 2
        }
        response = self.client.post(url, data)
        self.assertTrue(StudyTask.objects.filter(task_name="New Task").exists())

    def test_add_duplicate_task(self):
        response = self.client.post(reverse('add_task'), {
            'task_name': "Test Task",
            'class_name': "Math",
            'duration': 30,
            'deadline': (timezone.now() + timezone.timedelta(hours=5)).strftime('%Y-%m-%dT%H:%M'),
            'importance': 2,
            'difficulty': 2
        })
        self.assertContains(response, "already exists")

    def test_delete_task(self):
        response = self.client.post(reverse('delete_task', args=[self.task.id]), follow=True)
        self.assertFalse(StudyTask.objects.filter(id=self.task.id).exists())

    def test_edit_task(self):
        task = StudyTask.objects.create(
            task_name="Editable Task",
            class_name="Math",
            duration=60,
            deadline=(timezone.now() + timezone.timedelta(days=2)),
            importance=4,
            difficulty=3
        )

        url = reverse("edit_task", args=[task.id])
        data = {
            "task_name": "Updated Task",
            "class_name": "Math",
            "duration": 75,
            "deadline": (timezone.now() + timezone.timedelta(days=3)).strftime('%Y-%m-%dT%H:%M'),
            "importance": 5,
            "difficulty": 4
        }
        self.client.post(url, data)
        updated = StudyTask.objects.get(id=task.id)
        self.assertEqual(updated.task_name, "Updated Task")

    def test_complete_task(self):
        response = self.client.get(reverse('complete_task', args=[self.task.id]), follow=True)
        self.assertFalse(StudyTask.objects.filter(id=self.task.id).exists())
