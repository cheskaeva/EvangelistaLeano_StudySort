from django.shortcuts import render, redirect, get_object_or_404
from django import forms
from django.contrib import messages
from django.utils import timezone
from .models import StudyTask

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

# Form
class StudyTaskForm(forms.ModelForm):
    class Meta:
        model = StudyTask
        fields = ['task_name','class_name','duration','deadline','importance','difficulty']
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type':'datetime-local'}),
            'importance': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'difficulty': forms.NumberInput(attrs={'min': 1, 'max': 5}), 
        }
        
    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        if deadline and deadline < timezone.now():
            raise forms.ValidationError("Deadline cannot be in the past.")
        return deadline

# Sorting Algorithms
# (1) Merge Sort
def merge_sort(tasks):
    if len(tasks) <= 1:
        return tasks 
    
    mid = len(tasks) // 2
    left = merge_sort(tasks[:mid]) 
    right = merge_sort(tasks[mid:]) 
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0

    while i < len(left) and j < len(right):
        if left[i].priority_score >= right[j].priority_score:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    result.extend(left[i:])
    result.extend(right[j:])
    return result 

# (2) Insertion Sort 
def insertion_sort_single(sorted_tasks, new_task):
    insert_position = len(sorted_tasks)

    for i, task in enumerate(sorted_tasks):
        if new_task.priority_score > task.priority_score:
            insert_position = i
            break
    
    sorted_tasks.insert(insert_position, new_task)
    return sorted_tasks 

# Data Structures 
# Hash Table 
def check_duplicate_task(class_name, task_name, exclude_id=None):
    query = StudyTask.objects.filter(class_name = class_name, task_name = task_name)

    if exclude_id:
        query = query.exclude(id = exclude_id)
    return query.exists()

# View Functions 
def index(request):

    # Checks for cached sorted list in session
    if 'sorted_task_ids' in request.session:
        sorted_ids = request.session['sorted_task_ids']
        sorted_tasks = []

        for task_id in sorted_ids:
            if StudyTask.objects.filter(id=task_id).exists():
                task = StudyTask.objects.get(id=task_id)
                sorted_tasks.append(task)
                # Reads from cache 
                
    else:
        tasks = list(StudyTask.objects.all())
        if tasks:
            sorted_tasks = merge_sort(tasks)
        else:
            sorted_tasks = []
        request.session['sorted_task_ids'] = [t.id for t in sorted_tasks] 
        # Creates the cache
        # Gets id of each task in sorted_tasks 

    context = {
        'tasks': sorted_tasks,
        'task_count': len(sorted_tasks)
    }

    return render(request, 'studysort_app/index.html', context)

def add_task(request):
    if request.method == "POST":
        task_name = request.POST.get('task_name', '')
        class_name = request.POST.get('class_name', '')

        if check_duplicate_task(class_name, task_name):
            messages.error(
                request,
                f"🟡 Task '{task_name}' already exists in {class_name}."
            )
            return render(request, 'studysort_app/add_task.html', {
                'current_datetime': timezone.now().strftime('%Y-%m-%dT%H:%M')
            })
        
        form = StudyTaskForm(request.POST)
        if form.is_valid():
            new_task = form.save()
            
            if 'sorted_task_ids' in request.session:
                sorted_ids = request.session['sorted_task_ids']

                sorted_tasks = []
                for task_id in sorted_ids:
                    if StudyTask.objects.filter(id=task_id).exists():
                        task = StudyTask.objects.get(id=task_id)
                        sorted_tasks.append(task)
                        # Reads from cache 
                
                sorted_tasks = insertion_sort_single(sorted_tasks, new_task) # insert sort
                request.session['sorted_task_ids'] = [t.id for t in sorted_tasks] # update cache

            else:
                # No cache exists
                all_tasks = list(StudyTask.objects.all())
                sorted_tasks = merge_sort(all_tasks)
                request.session['sorted_task_ids'] = [t.id for t in sorted_tasks] # create cache

            messages.success(request, f"🟢 Task '{task_name}' added to '{class_name}' successfully!")
            return redirect('index')
        
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = StudyTaskForm()

    current_datetime = timezone.now().strftime('%Y-%m-%dT%H:%M')
    return render(request, 'studysort_app/add_task.html', {
        'form': form,
        'current_datetime': current_datetime
    })

def delete_task(request, task_id):
    task = get_object_or_404(StudyTask, id=task_id)
    
    if request.method == "POST":
        task_name = task.task_name
        class_name = task.class_name
        task.delete()  

        if 'sorted_task_ids' in request.session:
            del request.session['sorted_task_ids']

        messages.success(request, f"🗑 Task '{task_name}' from {class_name} deleted successfully!")
        return redirect('index')
    
    return render(request, 'studysort_app/delete_task.html', {'task': task})

def edit_task(request, task_id):
    task = get_object_or_404(StudyTask, id=task_id)
    
    if request.method == "POST":
        form = StudyTaskForm(request.POST, instance=task)
        
        if form.is_valid():
            form.save()

            if 'sorted_task_ids' in request.session:
                del request.session['sorted_task_ids']

            messages.success(request, f"Task '{task.task_name}' updated successfully!")
            return redirect('index')
    else:
        form = StudyTaskForm(instance=task)
    
    return render(request, 'studysort_app/edit_task.html', {
        'task': task,
        'form': form
    })

def complete_task(request, task_id):
    task = get_object_or_404(StudyTask, id=task_id)
    task_name = task.task_name
    task.delete()

    if 'sorted_task_ids' in request.session:
            del request.session['sorted_task_ids']

    messages.success(request, f"🎉 Completed task '{task_name}'! Great job!")
    return redirect('index')

# Additional Features 
def hide_tutorial(request):
    request.session['hide_how_it_works'] = True
    return redirect('index')

def show_tutorial(request):
    if 'hide_how_it_works' in request.session:
        del request.session['hide_how_it_works']
    return redirect('index')
