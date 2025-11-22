from django.shortcuts import render, redirect, get_object_or_404
from django import forms
from django.contrib import messages
from .models import StudyTask
import re

# form class for add StudyTask
class StudyTaskForm(forms.ModelForm):
    class Meta:
        model = StudyTask
        fields = ['task_name','class_name','duration','deadline','importance','difficulty']
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type':'datetime-local'}),
            'importance': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'difficulty': forms.NumberInput(attrs={'min': 1, 'max': 5}), 
        }

def index(request):
    return render(request, 'studysort_app/index.html')

def add_task(request):
    if request.method == "POST":
        form = StudyTaskForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('results')
    else:
        form = StudyTaskForm
    
    return render(request, 'studysort_app/add_task.html', {'form': form})

def results(request):
    tasks = StudyTask.objects.all()
    sorted_tasks = sorted(tasks, key=lambda t: t.priority_score, reverse=True)

    return render(request, 'studysort_app/results.html', {'tasks': sorted_tasks})