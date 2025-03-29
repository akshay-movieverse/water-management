from django.utils import timezone
from django.shortcuts import render, redirect
from django.db.models import Max
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now, timedelta
from .models import MonthlyOpeningSub, RechargeUnitDailyReading, RechargeUnitMonthlyOpening, Subunit, DailyReading, Attendance, Expense, Worker
from admin_dashboard.models import RechargeUnit, ReportGeneration, ResetHistory, Unit


def is_date_allowed(date, unit):
    """Check if date is within last 3 days + today AND after last reset"""
    # Get last reset date for the unit
    last_reset = ResetHistory.objects.filter(
        Q(action_type__in=['subunit_reset_plus', 'recharge_fill_plus']) &
        Q(is_undo=False) &
        (Q(monthlyopeningsub__subunit__unit=unit) |
         Q(rechargeunitmonthlyopening__recharge_unit__unit=unit))
    ).aggregate(last_date=Max('date')).get('last_date')

    # Original 3-day window dates
    today = now().date()
    three_days_ago = today - timedelta(days=3)
    original_dates = {three_days_ago + timedelta(days=i) for i in range(4)}

    #print("Last reset date:", last_reset)
    # Calculate allowed dates
    if last_reset:
        
        # Intersection of original dates and dates >= reset
        allowed_dates = {d for d in original_dates if d > last_reset}
    else:
        allowed_dates = original_dates

    return date in allowed_dates


@login_required
def manager_dashboard(request):
    unit = request.user.unit
    today = now().date()
    three_days_ago = today - timedelta(days=3)
    
    # Generate possible dates and filter
    possible_dates = [three_days_ago + timedelta(days=i) for i in range(4)]
    allowed_dates = [date for date in possible_dates if is_date_allowed(date, unit)]

        # Get top 4 recent reports
    intervals = get_reset_intervals(request.user.unit)
    for interval in intervals:
        totals = calculate_interval_totals(
            request.user.unit, 
            interval['start'], 
            interval['end']
        )
        interval.update(totals)
    
    recent_reports = sorted(intervals, key=lambda x: x['end'], reverse=True)[:4]

    return render(request, 'manager_dashboard/dashboard.html', {
        'allowed_dates': reversed(allowed_dates),
        'recent_reports': recent_reports
    })

from django.contrib import messages
###############################################################################################
@login_required
def fill_daily_readings(request, date):
    date = timezone.datetime.strptime(date, "%Y-%m-%d").date()
    unit = request.user.unit
    if not is_date_allowed(date, unit):
        messages.error(request, "You can only fill readings for the last 3 days and today.")
        return redirect('manager_dashboard')

    
    subunits = Subunit.objects.filter(unit=unit)
    
    if request.method == 'POST':
        for subunit in subunits:
            # Get the latest monthly opening before or on the current date
            monthly_opening = MonthlyOpeningSub.objects.filter(
                subunit=subunit,
                date__lte=date
            ).order_by('-date').first()

            if monthly_opening:
                # Find the latest daily reading between the monthly opening and current date
                last_reading_after_opening = DailyReading.objects.filter(
                    subunit=subunit,
                    date__lt=date,
                    date__gte=monthly_opening.date
                ).order_by('-date').first()
                
                if last_reading_after_opening:
                    opening_amount = last_reading_after_opening.amount_closing_reading
                    opening_dispenser = last_reading_after_opening.dispenser_closing_reading
                else:
                    opening_amount = monthly_opening.amount_opening
                    opening_dispenser = monthly_opening.dispenser_opening
            else:
                # Fallback to last daily reading if no monthly opening exists
                last_reading = DailyReading.objects.filter(
                    subunit=subunit,
                    date__lt=date
                ).order_by('-date').first()
                opening_amount = last_reading.amount_closing_reading if last_reading else 0
                opening_dispenser = last_reading.dispenser_closing_reading if last_reading else 0

            # Rest of your existing POST processing logic...
            # [Keep the existing code for handling form data and validation]
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
        
        return redirect('fill_recharge_readings', date=date)

        #return redirect('fill_attendance', date=date)
    
    # Prepare subunit data with updated opening values
    subunit_data = []
    for subunit in subunits:
        monthly_opening = MonthlyOpeningSub.objects.filter(
            subunit=subunit,
            date__lte=date
        ).order_by('-date').first()

        if monthly_opening:
            last_reading_after_opening = DailyReading.objects.filter(
                subunit=subunit,
                date__lt=date,
                date__gte=monthly_opening.date
            ).order_by('-date').first()
            
            if last_reading_after_opening:
                opening_amount = last_reading_after_opening.amount_closing_reading
                opening_dispenser = last_reading_after_opening.dispenser_closing_reading
            else:
                opening_amount = monthly_opening.amount_opening
                opening_dispenser = monthly_opening.dispenser_opening
        else:
            last_reading = DailyReading.objects.filter(
                subunit=subunit,
                date__lt=date
            ).order_by('-date').first()
            opening_amount = last_reading.amount_closing_reading if last_reading else 0
            opening_dispenser = last_reading.dispenser_closing_reading if last_reading else 0

        current_reading = DailyReading.objects.filter(date=date, subunit=subunit).first()
        
        subunit_data.append({
            'subunit': subunit,
            'opening_amount': opening_amount,
            'opening_dispenser': opening_dispenser,
            'closing_amount': current_reading.amount_closing_reading if current_reading else None,
            'closing_dispenser': current_reading.dispenser_closing_reading if current_reading else None,
        })
    
    return render(request, 'manager_dashboard/fill_readings.html', {
        'subunit_data': subunit_data,
        'date': date,
    })

# @login_required
# def fill_daily_readings(request, date):

#     date = timezone.datetime.strptime(date, "%Y-%m-%d").date()

#     if not is_date_allowed(date):
#         messages.error(request, "You can only fill readings for the last 3 days and today.")
#         return redirect('manager_dashboard')


#     unit = request.user.unit
#     subunits = Subunit.objects.filter(unit=unit)
    
#     if request.method == 'POST':
#         for subunit in subunits:
#             # Get the last reading for the subunit to use as opening values
#             last_reading = DailyReading.objects.filter(date__lt=date, subunit=subunit).order_by('-date').first()
#             opening_amount = last_reading.amount_closing_reading if last_reading else 0
#             opening_dispenser = last_reading.dispenser_closing_reading if last_reading else 0

#             # Get the closing values from the form
#             closing_amount_str = request.POST.get(f'closing_amount_{subunit.id}', '')
#             closing_dispenser_str = request.POST.get(f'closing_dispenser_{subunit.id}', '')

#             # Skip if both fields are empty
#             if not closing_amount_str and not closing_dispenser_str:
#                 continue

#             # Check if one field is filled and the other is empty
#             if (closing_amount_str and not closing_dispenser_str) or (not closing_amount_str and closing_dispenser_str):
#                 messages.error(request, f"Both fields for {subunit.name} must be filled or left empty.")
#                 return redirect('fill_daily_readings', date=date)

#             # Convert closing values to integers
#             closing_amount = int(closing_amount_str) if closing_amount_str else 0
#             closing_dispenser = int(closing_dispenser_str) if closing_dispenser_str else 0

#             # Validate closing values
#             if closing_amount < opening_amount or closing_dispenser < opening_dispenser:
#                 messages.error(request, f"Closing readings for {subunit.name} cannot be less than opening readings.")
#                 return redirect('fill_daily_readings', date=date)

#             # Update or create the daily reading
#             DailyReading.objects.update_or_create(
#                 date=date, subunit=subunit,
#                 defaults={
#                     'amount_opening_reading': opening_amount,
#                     'dispenser_opening_reading': opening_dispenser,
#                     'amount_closing_reading': closing_amount,
#                     'dispenser_closing_reading': closing_dispenser
#                 }
#             )
        
#         return redirect('fill_attendance', date=date)
    
#     # Prepare subunit data for the template
#     subunit_data = []
#     for subunit in subunits:
#         # Get the last reading before the current date for opening values
#         last_reading = DailyReading.objects.filter(date__lt=date, subunit=subunit).order_by('-date').first()
#         # Get the current date's reading (if it exists)
#         current_reading = DailyReading.objects.filter(date=date, subunit=subunit).first()
        
#         subunit_data.append({
#             'subunit': subunit,
#             'opening_amount': last_reading.amount_closing_reading if last_reading else 0,
#             'opening_dispenser': last_reading.dispenser_closing_reading if last_reading else 0,
#             'closing_amount': current_reading.amount_closing_reading if current_reading else None,
#             'closing_dispenser': current_reading.dispenser_closing_reading if current_reading else None,
#         })
    
#     return render(request, 'manager_dashboard/fill_readings.html', {
#         'subunit_data': subunit_data,
#         'date': date,
#     })





from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Worker, Attendance

@login_required
def fill_attendance(request, date):
    date = timezone.datetime.strptime(date, "%Y-%m-%d").date()
    unit = request.user.unit
    if not is_date_allowed(date, unit):
        messages.error(request, "You can only fill attendance for the last 3 days and today.")
        return redirect('manager_dashboard')

    
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
    unit = request.user.unit
    if not is_date_allowed(date,unit):
        messages.error(request, "You can only fill expenses for the last 3 days and today.")
        return redirect('manager_dashboard')
    

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
    unit = request.user.unit
    if not is_date_allowed(date, unit):
        messages.error(request, "You can only generate reports for the last 3 days and today.")
        return redirect('manager_dashboard')
    

    subunit_readings = DailyReading.objects.filter(date=date, subunit__unit=unit)
    recharge_readings = RechargeUnitDailyReading.objects.filter(date=date, recharge_unit__unit=unit)
    expenses = Expense.objects.filter(date=date, unit=unit)
    attendance = Attendance.objects.filter(date=date, worker__unit=unit)

    # Calculate totals
    subunit_income = sum(r.amount_rs() for r in subunit_readings)
    recharge_income = sum(r.amount_rs() for r in recharge_readings)
    total_income = subunit_income + recharge_income
    total_expense = sum(e.amount for e in expenses)
    total_water_supply = sum(r.water_supply() for r in subunit_readings)
    cash_in_hand = total_income - total_expense

    # Check if a report for this date already exists
    report, created = ReportGeneration.objects.update_or_create(
        manager=request.user,
        unit=unit,
        date=date,
        defaults={'generated_at': timezone.now()}
    )
    
    return render(request, 'manager_dashboard/report.html', {
        'date': date,
        'unit': unit,
        'subunit_readings': subunit_readings,
        'recharge_readings': recharge_readings,
        'expenses': expenses,
        'attendance': attendance,
        'subunit_income': subunit_income,
        'recharge_income': recharge_income,
        'total_income': total_income,
        'total_expense': total_expense,
        'total_water_supply': total_water_supply,
        'cash_in_hand': cash_in_hand,
    })

# @login_required
# def generate_report(request, date):
#     date = timezone.datetime.strptime(date, "%Y-%m-%d").date()

#     if not is_date_allowed(date):
#         messages.error(request, "You can only generate reports for the last 3 days and today.")
#         return redirect('manager_dashboard')
    
#     unit = request.user.unit
#     subunit_readings = DailyReading.objects.filter(date=date, subunit__unit=unit)
#     expenses = Expense.objects.filter(date=date, unit=unit)
#     attendance = Attendance.objects.filter(date=date, worker__unit=unit)

#     total_income = sum(r.amount_rs() for r in subunit_readings)  # Call method with ()
#     total_expense = sum(e.amount for e in expenses)
#     total_water_supply = sum(r.water_supply() for r in subunit_readings)  # Call method with ()
#     cash_in_hand = total_income - total_expense

#     # Check if a report for this date already exists
#     report, created = ReportGeneration.objects.update_or_create(
#         manager=request.user,
#         unit=unit,
#         date=date,
#         defaults={'generated_at': timezone.now()}  # Updates timestamp
#     )
    
#     return render(request, 'manager_dashboard/report.html', {
#         'date': date,
#         'unit': unit,
#         'subunit_readings': subunit_readings,
#         'expenses': expenses,
#         'attendance': attendance,
#         'total_income': total_income,
#         'total_expense': total_expense,
#         'total_water_supply': total_water_supply,  # Pass it to template
#         'cash_in_hand': cash_in_hand,
#     })



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



##############################################Recharge Unit

# @login_required
# def fill_recharge_readings(request, date):
#     date = timezone.datetime.strptime(date, "%Y-%m-%d").date()

#     if not is_date_allowed(date):
#         messages.error(request, "You can only fill readings for the last 3 days and today.")
#         return redirect('manager_dashboard')

#     unit = request.user.unit
#     recharge_units = RechargeUnit.objects.filter(unit=unit)

#     if request.method == 'POST':
#         for recharge_unit in recharge_units:
#             # Get last reading before current date to determine opening
#             last_reading = RechargeUnitDailyReading.objects.filter(
#                 date__lt=date, 
#                 recharge_unit=recharge_unit
#             ).order_by('-date').first()

#             opening = last_reading.closing_reading if last_reading else 0 #recharge_unit.initial_opening

#             closing_str = request.POST.get(f'closing_{recharge_unit.id}', '')
#             if not closing_str.strip():
#                 continue  # Skip if empty

#             try:
#                 closing = int(closing_str)
#             except ValueError:
#                 messages.error(request, f"Invalid value for {recharge_unit.name}.")
#                 return redirect('fill_recharge_readings', date=date)

#             if closing < 0:
#                 messages.error(request, f"Closing reading for {recharge_unit.name} cannot be negative.")
#                 return redirect('fill_recharge_readings', date=date)

#             if closing > opening:
#                 messages.error(request, f"Closing reading for {recharge_unit.name} cannot exceed opening ({opening}).")
#                 return redirect('fill_recharge_readings', date=date)

#             # Update or create the daily reading
#             RechargeUnitDailyReading.objects.update_or_create(
#                 date=date,
#                 recharge_unit=recharge_unit,
#                 defaults={
#                     'opening_reading': opening,
#                     'closing_reading': closing,
#                 }
#             )
        
#         return redirect('fill_attendance', date=date)  # Adjust redirect as needed

#     # Prepare data for template
#     recharge_unit_data = []
#     for recharge_unit in recharge_units:
#         last_reading = RechargeUnitDailyReading.objects.filter(
#             date__lt=date, 
#             recharge_unit=recharge_unit
#         ).order_by('-date').first()

#         current_reading = RechargeUnitDailyReading.objects.filter(
#             date=date,
#             recharge_unit=recharge_unit
#         ).first()

#         opening = last_reading.closing_reading if last_reading else 0 #recharge_unit.initial_opening
#         closing = current_reading.closing_reading if current_reading else None

#         recharge_unit_data.append({
#             'recharge_unit': recharge_unit,
#             'opening': opening,
#             'closing': closing,
#         })

#     return render(request, 'manager_dashboard/fill_recharge_readings.html', {
#         'recharge_unit_data': recharge_unit_data,
#         'date': date,
#     })

@login_required
def fill_recharge_readings(request, date):
    date = timezone.datetime.strptime(date, "%Y-%m-%d").date()
    unit = request.user.unit
    if not is_date_allowed(date,unit):
        messages.error(request, "You can only fill readings for the last 3 days and today.")
        return redirect('manager_dashboard')


    recharge_units = RechargeUnit.objects.filter(unit=unit)

    if request.method == 'POST':
        for recharge_unit in recharge_units:
            # Get monthly opening logic
            monthly_opening = RechargeUnitMonthlyOpening.objects.filter(
                recharge_unit=recharge_unit,
                date__lte=date
            ).order_by('-date').first()

            if monthly_opening:
                # Find readings between monthly opening and current date
                last_reading_after_opening = RechargeUnitDailyReading.objects.filter(
                    recharge_unit=recharge_unit,
                    date__lt=date,
                    date__gte=monthly_opening.date
                ).order_by('-date').first()

                if last_reading_after_opening:
                    opening = last_reading_after_opening.closing_reading
                else:
                    opening = monthly_opening.opening_reading
            else:
                # Fallback to last daily reading
                last_reading = RechargeUnitDailyReading.objects.filter(
                    recharge_unit=recharge_unit,
                    date__lt=date
                ).order_by('-date').first()
                opening = last_reading.closing_reading if last_reading else 0

            closing_str = request.POST.get(f'closing_{recharge_unit.id}', '')
            if not closing_str.strip():
                continue  # Skip if empty

            try:
                closing = int(closing_str)
            except ValueError:
                messages.error(request, f"Invalid value for {recharge_unit.name}.")
                return redirect('fill_recharge_readings', date=date)

            if closing < 0:
                messages.error(request, f"Closing reading for {recharge_unit.name} cannot be negative.")
                return redirect('fill_recharge_readings', date=date)

            if closing > opening:
                messages.error(request, f"Closing reading for {recharge_unit.name} cannot exceed opening ({opening}).")
                return redirect('fill_recharge_readings', date=date)

            # Update or create the daily reading
            RechargeUnitDailyReading.objects.update_or_create(
                date=date,
                recharge_unit=recharge_unit,
                defaults={
                    'opening_reading': opening,
                    'closing_reading': closing,
                }
            )
        
            # Rest of existing POST processing...
            # [Keep existing form handling logic]

        return redirect('fill_attendance', date=date)

    # Prepare data with monthly opening logic
    recharge_unit_data = []
    for recharge_unit in recharge_units:
        monthly_opening = RechargeUnitMonthlyOpening.objects.filter(
            recharge_unit=recharge_unit,
            date__lte=date
        ).order_by('-date').first()

        if monthly_opening:
            last_reading_after_opening = RechargeUnitDailyReading.objects.filter(
                recharge_unit=recharge_unit,
                date__lt=date,
                date__gte=monthly_opening.date
            ).order_by('-date').first()

            if last_reading_after_opening:
                opening = last_reading_after_opening.closing_reading
            else:
                opening = monthly_opening.opening_reading
        else:
            last_reading = RechargeUnitDailyReading.objects.filter(
                recharge_unit=recharge_unit,
                date__lt=date
            ).order_by('-date').first()
            opening = last_reading.closing_reading if last_reading else 0

        current_reading = RechargeUnitDailyReading.objects.filter(
            date=date,
            recharge_unit=recharge_unit
        ).first()

        recharge_unit_data.append({
            'recharge_unit': recharge_unit,
            'opening': opening,
            'closing': current_reading.closing_reading if current_reading else None,
        })

    return render(request, 'manager_dashboard/fill_recharge_readings.html', {
        'recharge_unit_data': recharge_unit_data,
        'date': date,
    })









def calculate_interval_totals(unit, start_date, end_date):
    """Calculate totals for a given date range"""
    # Subunit calculations
    subunit_readings = DailyReading.objects.filter(
        subunit__unit=unit,
        date__range=[start_date, end_date]
    )
    subunit_total = sum(r.amount_rs() for r in subunit_readings)
    water_supply = sum(r.water_supply() for r in subunit_readings)
    
    # Recharge calculations
    recharge_readings = RechargeUnitDailyReading.objects.filter(
        recharge_unit__unit=unit,
        date__range=[start_date, end_date]
    )
    recharge_total = sum(r.amount_rs() for r in recharge_readings)
    
    # Expense calculations
    expenses = Expense.objects.filter(
        unit=unit,
        date__range=[start_date, end_date]
    )
    expense_total = sum(e.amount for e in expenses)
    
    return {
        'subunit_total': subunit_total,
        'recharge_total': recharge_total,
        'expense_total': expense_total,
        'net_income': (subunit_total + recharge_total) - expense_total,
        'water_supply': water_supply
    }






from datetime import datetime, timedelta

from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from dateutil.relativedelta import relativedelta

@login_required
def generate_monthly_report(request,  start_date=None, end_date=None):
    unit = request.user.unit
    # start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    # end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    # Date validation
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            messages.error(request, "Invalid date format")
            return redirect('report_intervals')
        
        # Verify date range is valid
        valid_intervals = get_reset_intervals(unit)
        valid = any(
            interval['start'] <= start_date and interval['end'] >= end_date
            for interval in valid_intervals
        )
        
        if not valid:
            messages.error(request, "Invalid date range selected")
            return redirect('report_intervals')
    
    # Subunit Data Aggregation
    subunits = Subunit.objects.filter(unit=unit)
    subunit_data = []
    total_subunit_income = 0
    total_water_supply = 0
    for subunit in subunits:
        readings = DailyReading.objects.filter(
            subunit=subunit,
            date__range=[start_date, end_date]
        )
        subunit_amount = sum(r.amount_rs() for r in readings)
        water_supply = sum(r.water_supply() for r in readings)
        subunit_data.append({
            'subunit': subunit,
            'total_amount': subunit_amount,
            'total_water': water_supply,
        })
        total_subunit_income += subunit_amount
        total_water_supply += water_supply
    
    # Recharge Unit Data Aggregation
    recharge_units = RechargeUnit.objects.filter(unit=unit)
    recharge_data = []
    total_recharge_income = 0
    for recharge_unit in recharge_units:
        readings = RechargeUnitDailyReading.objects.filter(
            recharge_unit=recharge_unit,
            date__range=[start_date, end_date]
        )
        recharge_amount = sum(r.amount_rs() for r in readings)
        recharge_data.append({
            'recharge_unit': recharge_unit,
            'total_amount': recharge_amount,
        })
        total_recharge_income += recharge_amount
    
    # Expenses Aggregation
    expenses = Expense.objects.filter(
        unit=unit,
        date__range=[start_date, end_date]
    )
    expense_categories = {}
    for expense in expenses:
        category = expense.get_category_display()
        expense_categories[category] = expense_categories.get(category, 0) + expense.amount
    
    # Attendance Aggregation
    workers = Worker.objects.filter(unit=unit)
    attendance_data = []
    for worker in workers:
        present_days = Attendance.objects.filter(
            worker=worker,
            date__range=[start_date, end_date],
            is_present=True
        ).count()
        attendance_data.append({'worker': worker, 'present_days': present_days})
    
    # Totals
    total_income = total_subunit_income + total_recharge_income
    total_expense = sum(expense_categories.values(), 0)
    cash_in_hand = total_income - total_expense
    
    context = {
        #'month': month_date.strftime("%B %Y"),
        'subunit_data': subunit_data,
        'recharge_data': recharge_data,
        'expense_categories': expense_categories,
        'attendance_data': attendance_data,
        'total_subunit_income': total_subunit_income,
        'total_recharge_income': total_recharge_income,
        'total_income': total_income,
        'total_expense': total_expense,
        'cash_in_hand': cash_in_hand,
        'total_water_supply': total_water_supply,
        'unit': unit,
        'start_date': start_date,
        'end_date': end_date
    }
    return render(request, 'manager_dashboard/monthly_report.html', context)





from django.db.models import Q

def get_reset_intervals(unit):
    # Get all reset+ actions for the unit
    resets = ResetHistory.objects.filter(
        Q(action_type='subunit_reset_plus') &
        Q(is_undo=False) &
        (
            Q(monthlyopeningsub__subunit__unit=unit) | 
            Q(rechargeunitmonthlyopening__recharge_unit__unit=unit)
        )
    ).order_by('date').distinct()
    
    intervals = []
    
    # Get first reading date as initial start
    first_reading = DailyReading.objects.filter(subunit__unit=unit).order_by('date').first()
    start_date = first_reading.date if first_reading else timezone.now().date()
    
    for reset in resets:
        intervals.append({
            'start': start_date,
            'end': reset.date,
            'reset': reset
        })
        start_date = reset.date + timedelta(days=1)
    
    # Add current active interval
    # if start_date <= timezone.now().date():
    #     intervals.append({
    #         'start': start_date,
    #         'end': timezone.now().date(),
    #         'reset': None
    #     })
    
    return intervals

@login_required
def report_intervals(request):
    unit = request.user.unit
    intervals = get_reset_intervals(unit)
    
    # Month/Year filtering
    month_filter = request.GET.get('month')
    if month_filter:
        try:
            filter_date = datetime.strptime(month_filter, "%Y-%m").date()
            start_month = filter_date.replace(day=1)
            end_month = (start_month + relativedelta(months=1)) - relativedelta(days=1)
            
            # Filter intervals overlapping with month
            intervals = [
                i for i in intervals
                if not (i['end'] < start_month or i['start'] > end_month)
            ]
        except ValueError:
            messages.error(request, "Invalid month format")
    
    # Calculate totals
    for interval in intervals:
        totals = calculate_interval_totals(
            unit, interval['start'], interval['end']
        )
        interval.update(totals)
    
    # Pagination and ordering
    intervals = sorted(intervals, key=lambda x: x['end'], reverse=True)
    paginator = Paginator(intervals, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'manager_dashboard/report_intervals.html', {
        'page_obj': page_obj,
        'unit': unit,
        'selected_month': month_filter
    })