from django.urls import path
from .views import (
    add_worker, delete_worker, edit_worker, manager_dashboard, fill_daily_readings, fill_attendance, 
    fill_expenses, generate_report, workers_list
)

urlpatterns = [
    path('', manager_dashboard, name='manager_dashboard'),
    path('fill-daily-readings/<str:date>/', fill_daily_readings, name='fill_daily_readings'),
    path('fill-attendance/<str:date>/', fill_attendance, name='fill_attendance'),
    path('fill-expenses/<str:date>/', fill_expenses, name='fill_expenses'),
    path('generate-report/<str:date>/', generate_report, name='generate_report'),
    
    # Add Worker
    path('add-worker/', add_worker, name='add_worker'),
    
    path('workers/', workers_list, name='workers_list'),
    path('workers/edit/<int:worker_id>/', edit_worker, name='edit_worker'),
    path('workers/delete/<int:worker_id>/', delete_worker, name='delete_worker'),
    path('workers/add/', add_worker, name='add_worker'),

]
