from django.db import models

# Create your models here.

class StudyTask(models.Model):
    task_name = models.CharField(max_length=200)
    class_name = models.CharField(max_length=200)
    duration = models.IntegerField(help_text="Minutes needed")
    deadline = models.DateTimeField()
    importance = models.IntegerField(help_text="1 = Low, 5 = High") #can this be drop down?
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

    

