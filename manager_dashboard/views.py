from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now, timedelta
from .models import Subunit, DailyReading, Attendance, Expense, Worker
from admin_dashboard.models import ReportGeneration, Unit


def is_date_allowed(date):
    """Check if the given date is within the allowed range (last 3 days + today)."""
    today = now().date()
    three_days_ago = today - timedelta(days=3)
    allowed_dates = {three_days_ago + timedelta(days=i) for i in range(4)}
    return date in allowed_dates



@login_required
def manager_dashboard(request):
    today = now().date()
    three_days_ago = today - timedelta(days=3)
    allowed_dates = reversed([three_days_ago + timedelta(days=i) for i in range(4)])
    
    return render(request, 'manager_dashboard/dashboard.html', {
        'allowed_dates': allowed_dates,
    })

from django.contrib import messages

@login_required
def fill_daily_readings(request, date):

    date = timezone.datetime.strptime(date, "%Y-%m-%d").date()

    if not is_date_allowed(date):
        messages.error(request, "You can only fill readings for the last 3 days and today.")
        return redirect('manager_dashboard')


    unit = request.user.unit
    subunits = Subunit.objects.filter(unit=unit)
    
    if request.method == 'POST':
        for subunit in subunits:
            # Get the last reading for the subunit to use as opening values
            last_reading = DailyReading.objects.filter(date__lt=date, subunit=subunit).order_by('-date').first()
            opening_amount = last_reading.amount_closing_reading if last_reading else 0
            opening_dispenser = last_reading.dispenser_closing_reading if last_reading else 0

            # Get the closing values from the form
            closing_amount_str = request.POST.get(f'closing_amount_{subunit.id}', '')
            closing_dispenser_str = request.POST.get(f'closing_dispenser_{subunit.id}', '')

            # Skip if both fields are empty
            if not closing_amount_str and not closing_dispenser_str:
                continue

            # Check if one field is filled and the other is empty
            if (closing_amount_str and not closing_dispenser_str) or (not closing_amount_str and closing_dispenser_str):
                messages.error(request, f"Both fields for {subunit.name} must be filled or left empty.")
                return redirect('fill_daily_readings', date=date)

            # Convert closing values to integers
            closing_amount = int(closing_amount_str) if closing_amount_str else 0
            closing_dispenser = int(closing_dispenser_str) if closing_dispenser_str else 0

            # Validate closing values
            if closing_amount < opening_amount or closing_dispenser < opening_dispenser:
                messages.error(request, f"Closing readings for {subunit.name} cannot be less than opening readings.")
                return redirect('fill_daily_readings', date=date)

            # Update or create the daily reading
            DailyReading.objects.update_or_create(
                date=date, subunit=subunit,
                defaults={
                    'amount_opening_reading': opening_amount,
                    'dispenser_opening_reading': opening_dispenser,
                    'amount_closing_reading': closing_amount,
                    'dispenser_closing_reading': closing_dispenser
                }
            )
        
        return redirect('fill_attendance', date=date)
    
    # Prepare subunit data for the template
    subunit_data = []
    for subunit in subunits:
        # Get the last reading before the current date for opening values
        last_reading = DailyReading.objects.filter(date__lt=date, subunit=subunit).order_by('-date').first()
        # Get the current date's reading (if it exists)
        current_reading = DailyReading.objects.filter(date=date, subunit=subunit).first()
        
        subunit_data.append({
            'subunit': subunit,
            'opening_amount': last_reading.amount_closing_reading if last_reading else 0,
            'opening_dispenser': last_reading.dispenser_closing_reading if last_reading else 0,
            'closing_amount': current_reading.amount_closing_reading if current_reading else None,
            'closing_dispenser': current_reading.dispenser_closing_reading if current_reading else None,
        })
    
    return render(request, 'manager_dashboard/fill_readings.html', {
        'subunit_data': subunit_data,
        'date': date,
    })

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Worker, Attendance

@login_required
def fill_attendance(request, date):
    date = timezone.datetime.strptime(date, "%Y-%m-%d").date()

    if not is_date_allowed(date):
        messages.error(request, "You can only fill attendance for the last 3 days and today.")
        return redirect('manager_dashboard')

    unit = request.user.unit
    workers = Worker.objects.filter(unit=unit)

    # Fetch existing attendance records
    existing_attendance = Attendance.objects.filter(date=date, worker__in=workers)
    attendance_records = {record.worker.id: record.is_present for record in existing_attendance}

    if request.method == 'POST':
        for worker in workers:
            attendance_value = request.POST.get(f'worker_{worker.id}')
            is_present = True if attendance_value == 'present' else False

            # Update or create attendance record
            Attendance.objects.update_or_create(
                date=date, worker=worker,
                defaults={'is_present': is_present}
            )

        return redirect('fill_expenses', date=date)

    return render(request, 'manager_dashboard/fill_attendance.html', {
        'workers': workers,
        'date': date,
        'attendance_records': attendance_records
    })


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Expense

@login_required
def fill_expenses(request, date):
    date = timezone.datetime.strptime(date, "%Y-%m-%d").date()

    if not is_date_allowed(date):
        messages.error(request, "You can only fill expenses for the last 3 days and today.")
        return redirect('manager_dashboard')
    
    unit = request.user.unit
    categories = [
        'pickup_diesel', 'intra_v30_diesel', 'ace_new_diesel', 'diesel', 'salary',
        'electricity', 'plant_expense', 'petrol', 'nagar_palika', 'others'
    ]

    # Fetch existing expenses for the given date and unit
    existing_expenses = Expense.objects.filter(date=date, unit=unit)
    expense_dict = {expense.category: expense.amount for expense in existing_expenses}

    if request.method == 'POST':
        for category in categories:
            amount = request.POST.get(category, '0')
            amount = int(amount) if amount.strip() else 0  # Default to 0 if empty

            Expense.objects.update_or_create(
                date=date, unit=unit, category=category,
                defaults={'amount': amount}
            )

        return redirect('generate_report', date=date)

    return render(request, 'manager_dashboard/fill_expenses.html', {
        'categories': categories,
        'date': date,
        'expense_dict': expense_dict  # Pass existing data to the template
    })


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Expense, DailyReading, Attendance

@login_required
def generate_report(request, date):
    date = timezone.datetime.strptime(date, "%Y-%m-%d").date()

    if not is_date_allowed(date):
        messages.error(request, "You can only generate reports for the last 3 days and today.")
        return redirect('manager_dashboard')
    
    unit = request.user.unit
    subunit_readings = DailyReading.objects.filter(date=date, subunit__unit=unit)
    expenses = Expense.objects.filter(date=date, unit=unit)
    attendance = Attendance.objects.filter(date=date, worker__unit=unit)

    total_income = sum(r.amount_rs() for r in subunit_readings)  # Call method with ()
    total_expense = sum(e.amount for e in expenses)
    total_water_supply = sum(r.water_supply() for r in subunit_readings)  # Call method with ()
    cash_in_hand = total_income - total_expense

    # Check if a report for this date already exists
    report, created = ReportGeneration.objects.update_or_create(
        manager=request.user,
        unit=unit,
        date=date,
        defaults={'generated_at': timezone.now()}  # Updates timestamp
    )
    
    return render(request, 'manager_dashboard/report.html', {
        'date': date,
        'unit': unit,
        'subunit_readings': subunit_readings,
        'expenses': expenses,
        'attendance': attendance,
        'total_income': total_income,
        'total_expense': total_expense,
        'total_water_supply': total_water_supply,  # Pass it to template
        'cash_in_hand': cash_in_hand,
    })



from django.contrib import messages


@login_required
def add_worker(request):
    if request.method == 'POST':
        worker_names = request.POST.getlist('worker_name[]')
        for name in worker_names:
            if name.strip():
                Worker.objects.create(name=name.strip(), unit=request.user.unit)
        return redirect('add_worker')

    return render(request, 'manager_dashboard/add_worker.html')


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Worker

@login_required
def workers_list(request):
    workers = Worker.objects.filter(is_deleted=False, unit=request.user.unit)
    return render(request, 'manager_dashboard/workers.html', {'workers': workers})

@login_required
def edit_worker(request, worker_id):
    worker = get_object_or_404(Worker, id=worker_id, is_deleted=False, unit=request.user.unit)

    if request.method == 'POST':
        new_name = request.POST.get('name').strip()
        if new_name:
            worker.name = new_name
            worker.save()
        return redirect('workers_list')

    return render(request, 'manager_dashboard/edit_worker.html', {'worker': worker})

@login_required
def delete_worker(request, worker_id):
    worker = get_object_or_404(Worker, id=worker_id, is_deleted=False, unit=request.user.unit)

    if request.method == 'POST':
        worker.delete()
        return redirect('workers_list')

    return redirect('workers_list')
