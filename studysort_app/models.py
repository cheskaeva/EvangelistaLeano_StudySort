from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

# Create your models here.
class StudyTask(models.Model):
    task_name = models.CharField(max_length=200)
    class_name = models.CharField(max_length=200)
    duration = models.IntegerField(help_text="Minutes needed")
    deadline = models.DateTimeField()
    importance = models.IntegerField(help_text="1 = Low, 5 = High") 
    difficulty = models.IntegerField(help_text="1 = Low, 5 = High")

    def __str__(self):
        return self.task_name
    
    @property
    def duration_factor(self):
        d = self.duration

        if d <= 30:
            return 5 
        elif d <=60:
            return 4
        elif d <=90:
            return 3
        elif d <=120:
            return 2
        else:
            return 1

    @property
    def priority_score(self):
        return (self.difficulty * 2) + (self.importance * 3) + self.duration_factor
        
    def clean(self):
        super().clean()
        if self.deadline and self.deadline < timezone.now():
            raise ValidationError({'deadline': 'Deadline cannot be in the past.'})

    class Meta:
        unique_together = ['class_name', 'task_name'] 
        ordering = ['class_name', 'task_name'] 


    