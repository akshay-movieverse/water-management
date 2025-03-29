
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect

from manager_dashboard.views import calculate_interval_totals, get_reset_intervals
from .models import RechargeUnit, ReportGeneration, ResetHistory, Unit, Subunit, CustomUser

from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from django.shortcuts import render, redirect, get_object_or_404
from .models import Unit, Subunit, CustomUser
from .forms import UnitForm, SubunitForm, ManagerForm
from django.contrib.auth.decorators import login_required

@login_required
def admin_dashboard(request):
    # Get the current date and start of the week (Monday)
    today = timezone.now().date()
    # Find the Monday of current week
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    # Get all managers
    managers = reversed(CustomUser.objects.filter(is_manager=True, is_deleted=False).prefetch_related('unit'))
    
    # Prepare manager data with report statistics
    managers_data = []
    
    for manager in managers:
        # Get reports for this week
        week_reports = ReportGeneration.objects.filter(
            manager=manager,
            date__gte=start_of_week,
            date__lte=end_of_week
        )
        
        # Count reports by day of week
        # reports_by_day = {}
        # for i in range(7):
        #     day_date = start_of_week + timedelta(days=i)
        #     reports_by_day[i] = week_reports.filter(date=day_date).count()
        reports_by_day = {}
        subunit_counts_by_day = {}
        #print(manager.unit.subunit_set.all().count())
        for i in range(7):
            day_date = start_of_week + timedelta(days=i)
            reports_on_day = week_reports.filter(date=day_date)
            # Count the reports generated on this day
            reports_by_day[i] = reports_on_day.count()
            
            if reports_on_day.exists():
                # Count the number of unique subunits included in reports
                subunits_on_day = DailyReading.objects.filter(
                    date=day_date,
                    subunit__unit=manager.unit  # Filter by the manager's unit
                ).values('subunit').distinct().count()
            else:
                subunits_on_day = 0
                
            subunit_counts_by_day[i] = subunits_on_day    

        # Get latest report generation time
        last_report = ReportGeneration.objects.filter(manager=manager).order_by('-generated_at').first()
        
        # Calculate weekly submission percentage (if submitted every day = 100%)
        days_with_submissions = sum(1 for count in reports_by_day.values() if count > 0)
        weekly_submission_percentage = round((days_with_submissions / 7) * 100)
        
        # Add manager data
        manager_data = {
            'username': manager.username,
            'get_full_name': f"{manager.first_name} {manager.last_name}" if manager.first_name else manager.username,
            'unit': manager.unit,
            'is_online': (timezone.now() - manager.last_login).total_seconds() < 300 if manager.last_login else False,
            'last_login': manager.last_login,
            'weekly_submission_percentage': weekly_submission_percentage,
            'reports_monday': subunit_counts_by_day[0],
            'reports_tuesday': subunit_counts_by_day[1],
            'reports_wednesday': subunit_counts_by_day[2],
            'reports_thursday': subunit_counts_by_day[3],
            'reports_friday': subunit_counts_by_day[4],
            'reports_saturday': subunit_counts_by_day[5],
            'reports_sunday': subunit_counts_by_day[6],
            'reports_total': manager.unit.subunit_set.all().count(), #sum(reports_by_day.values()),
            'last_report_generated': last_report.generated_at if last_report else None,
            'week_start': start_of_week,
            'week_end': today  # Using today instead of end_of_week as you requested
        }
        
        managers_data.append(manager_data)
    
    context = {
        'managers': managers_data
    }
    
    return render(request, 'admin_dashboard/dashboard.html', context)

@login_required
def unit_list(request):
    units = Unit.objects.filter(is_deleted=False)
    return render(request, 'admin_dashboard/unit_list.html', {'units': units})

@login_required
def add_unit(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        city = request.POST.get('city')
        unit = Unit.objects.create(name=name, city=city)

        # Add Subunits
        subunit_names = request.POST.getlist('subunits[]')
        for subunit_name in subunit_names:
            if subunit_name.strip():
                Subunit.objects.create(unit=unit, name=subunit_name)

        # Add Recharge Units
        recharge_unit_names = request.POST.getlist('recharge_units[]')
        for recharge_name in recharge_unit_names:
            if recharge_name.strip():
                RechargeUnit.objects.create(unit=unit, name=recharge_name)

        messages.success(request, "Unit added successfully!")
        return redirect('unit_list')

    return render(request, 'admin_dashboard/add_unit.html')

@login_required
def edit_unit(request, unit_id):
    unit = get_object_or_404(Unit, id=unit_id, is_deleted=False)

    if request.method == 'POST':
        unit.name = request.POST.get('name')
        unit.city = request.POST.get('city')
        unit.save()
        return redirect('unit_list')

    return render(request, 'admin_dashboard/edit_unit.html', {'unit': unit})

@login_required
def unit_detail(request, unit_id):
    unit = get_object_or_404(Unit, id=unit_id, is_deleted=False)
    subunits = unit.subunit_set.filter(is_deleted=False)
    recharge_units = unit.recharge_units.filter(is_deleted=False)
    return render(request, 'admin_dashboard/unit_detail.html', {
        'unit': unit, 'subunits': subunits, 'recharge_units': recharge_units
    })

@login_required
def add_subunit_recharge(request, unit_id):
    unit = get_object_or_404(Unit, id=unit_id)

    if request.method == 'POST':
        # Add Subunits
        subunit_names = request.POST.getlist('subunits[]')
        for subunit_name in subunit_names:
            if subunit_name.strip():
                Subunit.objects.create(unit=unit, name=subunit_name)

        # Add Recharge Units
        recharge_unit_names = request.POST.getlist('recharge_units[]')
        for recharge_name in recharge_unit_names:
            if recharge_name.strip():
                RechargeUnit.objects.create(unit=unit, name=recharge_name)

        return redirect('unit_detail', unit_id=unit.id)

    return render(request, 'admin_dashboard/add_subunit_recharge.html', {'unit': unit})

@login_required
def delete_subunit(request, subunit_id):
    subunit = get_object_or_404(Subunit, id=subunit_id)
    unit_id = subunit.unit.id
    subunit.delete()
    return redirect('unit_detail', unit_id=unit_id)

@login_required
def delete_recharge_unit(request, recharge_unit_id):
    recharge_unit = get_object_or_404(RechargeUnit, id=recharge_unit_id)
    unit_id = recharge_unit.unit.id
    recharge_unit.delete()
    return redirect('unit_detail', unit_id=unit_id)

@login_required
def delete_unit(request, unit_id):
    unit = get_object_or_404(Unit, id=unit_id)
    unit.delete()
    return redirect('unit_list')

# @login_required
# def add_subunit(request, unit_id):
#     unit = get_object_or_404(Unit, id=unit_id)
#     if request.method == 'POST':
#         subunit_names = request.POST.getlist('subunits[]')
#         for subunit_name in subunit_names:
#             if subunit_name.strip():
#                 Subunit.objects.create(unit=unit, name=subunit_name)

#         return redirect('unit_detail', unit_id=unit.id)

#     return render(request, 'admin_dashboard/add_subunit.html', {'unit': unit})


@login_required
def delete_subunit(request, subunit_id):
    subunit = get_object_or_404(Subunit, id=subunit_id)
    subunit.delete()
    return redirect('unit_detail', unit_id=subunit.unit.id)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password
from .models import CustomUser, Unit


############################################################################################history


from django.core.paginator import Paginator

def history_view(request):
    history_list = ResetHistory.objects.order_by('-timestamp')
    paginator = Paginator(history_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'admin_dashboard/history.html', {'page_obj': page_obj})




def delete_reset(request, reset_id):
    if request.method == 'POST':
        reset = get_object_or_404(ResetHistory, id=reset_id)
        reset.delete()
        messages.success(request, 'History entry deleted successfully.')
    return redirect('history')




############################################################################################
@login_required
def manager_list(request):
    managers = CustomUser.objects.filter(is_manager=True)
    return render(request, 'admin_dashboard/manager_list.html', {'managers': managers})


from django.db import IntegrityError
from django.core.exceptions import ValidationError
@login_required
def add_manager(request):
    units = Unit.objects.filter(is_deleted=False).exclude(customuser__isnull=False)

    if request.method == "POST":
        name = request.POST.get('name')
        unit_id = request.POST.get('unit')
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        unit = get_object_or_404(Unit, id=unit_id) if unit_id else None

        # Check for duplicate username
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Username already exists. Choose another one.")
            return render(request, 'admin_dashboard/add_manager.html', {'units': units})

        # Check for duplicate email
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email already exists. Please use a different email.")
            return render(request, 'admin_dashboard/add_manager.html', {'units': units})

        try:
            manager = CustomUser.objects.create(
                username=username,
                first_name=name,
                is_manager=True,
                unit=unit,
                email=email or '',
                phone_number=phone or '',
                password=make_password(password)
            )
            messages.success(request, "Manager added successfully!")
            return redirect('manager_list')

        # except IntegrityError:
        #     messages.error(request, "A user with this email already exists.")
        #     return render(request, 'admin_dashboard/add_manager.html', {'units': units})

        except ValidationError as ve:
            messages.error(request, str(ve))

        except IntegrityError:
            messages.error(request, "A database error occurred. The email or username might already exist.")

        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {str(e)}")

    return render(request, 'admin_dashboard/add_manager.html', {'units': units})

from django.contrib.auth.hashers import make_password

@login_required
def edit_manager(request, manager_id):
    manager = get_object_or_404(CustomUser, id=manager_id, is_manager=True)
    units = Unit.objects.all()

    if request.method == "POST":
        manager.first_name = request.POST.get('name')
        unit_id = request.POST.get('unit')
        username = request.POST.get('username')
        manager.email = request.POST.get('email')
        manager.phone_number = request.POST.get('phone')
        new_password = request.POST.get('password')

        manager.unit = get_object_or_404(Unit, id=unit_id) if unit_id else None

        # Ensure unique username when editing
        if CustomUser.objects.filter(username=username).exclude(id=manager.id).exists():
            return render(request, 'admin_dashboard/edit_manager.html', {
                'manager': manager,
                'units': units,
                'error': 'Username already exists. Choose another one.'
            })

        manager.username = username

        # Change password if a new one is provided
        if new_password:
            manager.password = make_password(new_password)

        manager.save()

        return redirect('manager_list')

    return render(request, 'admin_dashboard/edit_manager.html', {'manager': manager, 'units': units})



@login_required
def delete_manager(request, manager_id):
    manager = get_object_or_404(CustomUser, id=manager_id, is_manager=True)
    manager.delete()
    messages.success(request, "Manager deleted successfully.")
    return redirect('manager_list')

###################################################################################################
from django.shortcuts import render, get_object_or_404
from manager_dashboard.models import Expense, DailyReading, Attendance, MonthlyOpeningSub, RechargeUnitDailyReading, RechargeUnitMonthlyOpening, Worker
from admin_dashboard.models import ReportGeneration

from django.shortcuts import render
from datetime import date
from .models import ReportGeneration, Unit

@login_required
def report_list(request):
    today = date.today()

    # Get filters from request
    selected_date = request.GET.get('date',timezone.now().date())
    selected_unit = request.GET.get('unit')

    # Query reports
    reports = ReportGeneration.objects.all().order_by('-date')

    if selected_date:
        reports = reports.filter(date=selected_date)

    if selected_unit:
        reports = reports.filter(unit_id=selected_unit)

    # Fetch all units for the dropdown
    units = Unit.objects.filter(is_deleted=False)

    # Get all unique dates where reports are available
    # Convert available report dates to string format (YYYY-MM-DD)
    available_dates = list(ReportGeneration.objects.values_list('date', flat=True).distinct())
    available_dates = [d.strftime('%Y-%m-%d') for d in available_dates]  # Convert to string
    #print(available_dates)

    return render(request, 'admin_dashboard/report_list.html', {
        'reports': reports,
        'units': units,
        'today': today,
        'available_dates': available_dates  # Pass dates to template
    })


@login_required
def report_detail(request, report_id):
    report = get_object_or_404(ReportGeneration, id=report_id)
    
    subunit_readings = DailyReading.objects.filter(date=report.date, subunit__unit=report.unit)
    recharge_readings = RechargeUnitDailyReading.objects.filter(date=report.date, recharge_unit__unit=report.unit)
    expenses = Expense.objects.filter(date=report.date, unit=report.unit)
    attendance = Attendance.objects.filter(date=report.date, worker__unit=report.unit)

    # Calculate totals
    subunit_income = sum(r.amount_rs() for r in subunit_readings)
    recharge_income = sum(r.amount_rs() for r in recharge_readings)
    total_income = subunit_income + recharge_income
    #total_income = sum(r.amount_rs() for r in subunit_readings)
    total_expense = sum(e.amount for e in expenses)
    total_water_supply = sum(r.water_supply() for r in subunit_readings)
    cash_in_hand = total_income - total_expense

    return render(request, 'admin_dashboard/admin_report.html', {
        'date': report.date,
        'report': report,
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



###################################################################################################

from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin


class GrandResetView(LoginRequiredMixin,TemplateView):
    template_name = 'admin_dashboard/grand_reset.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['units'] = Unit.objects.filter(is_deleted=False)
        return context
    
@login_required
def subunit_reset(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Prevent duplicate resets on same date
                if MonthlyOpeningSub.objects.filter(date=timezone.now().date(), reset_history__action_type="subunit_reset_plus").exists():
                    messages.warning(request, 'Subunits already reset today!')
                    return JsonResponse({'status': 'warning', 'message': 'Subunits already reset today!'})#redirect('grand_reset')

                # Create history record
                reset_history = ResetHistory.objects.create(
                    action_type='subunit_reset_plus',
                    date=timezone.now().date()
                )

                subunits = Subunit.objects.filter(
                    is_deleted=False
                ).exclude(
                    monthlyopeningsub__reset_history__date=timezone.now().date()
                )
                if not subunits.exists():
                    reset_history.delete()
                    messages.warning(request, 'No active subunits found to reset')
                    #return redirect('grand_reset')
                    return JsonResponse({'status': 'warning', 'message': 'No active subunits found to reset'})


                # Bulk create openings
                openings = [
                    MonthlyOpeningSub(
                        subunit=subunit,
                        date=reset_history.date,
                        amount_opening=0,
                        dispenser_opening=0,
                        reset_history=reset_history
                    )
                    for subunit in subunits
                ]
                MonthlyOpeningSub.objects.bulk_create(openings)
                
                messages.success(request, f'Successfully reset {len(subunits)} subunits!')

                # return redirect('grand_reset')
                return JsonResponse({'status': 'success', 'message': f'Successfully reset {len(subunits)} subunits!'})

        except Exception as e:
            messages.error(
                request, 
                f'Error resetting subunits: {str(e)}'
            )
            if reset_history:
                reset_history.delete()
            return JsonResponse({'status': 'error', 'message': f'Error resetting subunits: {str(e)}'})
            #return redirect('grand_reset')

    return redirect('grand_reset')


from django.db import transaction


class FillRechargeView(LoginRequiredMixin,TemplateView):
    template_name = 'admin_dashboard/fill_recharge.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        units = Unit.objects.filter(is_deleted=False).prefetch_related('recharge_units')
        
        # Prepare recharge units with their last closing readings
        for unit in units:
            unit.recharge_units_data = []
            for ru in unit.recharge_units.all():
                last_daily = RechargeUnitDailyReading.objects.filter(
                    recharge_unit=ru
                ).order_by('-date').first()
                unit.recharge_units_data.append({
                    'object': ru,
                    'last_closing': last_daily.closing_reading if last_daily else 0
                })
        
        context['units'] = units
        return context
    
    def post(self, request, *args, **kwargs):
        # Create ResetHistory record
        reset_history = ResetHistory.objects.create(
            action_type='recharge_fill_plus',
            date=timezone.now().date()
        )
        
        processed_count = 0
        recharge_units = RechargeUnit.objects.filter(is_deleted=False)
        
        for ru in recharge_units:
            ru_id = str(ru.id)
            opening_key = f'opening_{ru_id}'
            action_key = f'action_{ru_id}'
            
            if opening_key not in request.POST or request.POST[opening_key]=="" or  action_key not in request.POST:
                continue

            try:
                input_value = int(request.POST[opening_key])
                action = request.POST[action_key]
                
                # Get last closing reading
                last_daily = RechargeUnitDailyReading.objects.filter(
                    recharge_unit=ru
                ).order_by('-date').first()
                last_closing = last_daily.closing_reading if last_daily else 0
                
                # Calculate opening reading
                opening_reading = (last_closing + input_value) if action == 'add' else input_value
                
                # Update or create monthly opening
                RechargeUnitMonthlyOpening.objects.update_or_create(
                    recharge_unit=ru,
                    date=reset_history.date,
                    defaults={
                        'opening_reading': opening_reading,
                        'reset_history': reset_history
                    }
                )
                
                processed_count += 1
                
            except (ValueError, TypeError) as e:
                messages.error(request, f"Invalid input for {ru.name}: {e}")
                continue

        if processed_count > 0:
            messages.success(request, f"Successfully processed {processed_count} recharge units!")
        else:
            messages.warning(request, "No recharge units were processed")
            reset_history.delete()  # Clean up unused history

        return redirect('grand_reset')
    




###################################################################################################





class UnitSubunitsView(LoginRequiredMixin,TemplateView):
    template_name = 'admin_dashboard/unit_subunits.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        unit = get_object_or_404(Unit, pk=self.kwargs['unit_id'])
        context['unit'] = unit
        context['subunits'] = unit.subunit_set.filter(is_deleted=False)
        return context

class UnitRechargeUnitsView(LoginRequiredMixin,TemplateView):
    template_name = 'admin_dashboard/unit_recharge_units.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        unit = get_object_or_404(Unit, pk=self.kwargs['unit_id'])
        recharge_units = unit.recharge_units.filter(is_deleted=False)
        
        # Prepare recharge units with their last closing readings
        recharge_units_data = []
        for ru in recharge_units:
            last_daily = RechargeUnitDailyReading.objects.filter(
                recharge_unit=ru
            ).order_by('-date').first()
            recharge_units_data.append({
                'object': ru,
                'last_closing': last_daily.closing_reading if last_daily else 0
            })
        
        context['unit'] = unit
        context['recharge_units_data'] = recharge_units_data
        return context
    
    def post(self, request, *args, **kwargs):
        unit = get_object_or_404(Unit, pk=self.kwargs['unit_id'])
        recharge_units = unit.recharge_units.filter(is_deleted=False)
        with transaction.atomic():
                
            # Create ResetHistory record
            reset_history = ResetHistory.objects.create(
                action_type='recharge_fill',
                date=timezone.now().date()
            )
            
            processed_count = 0
            
            for ru_data in recharge_units:
                ru = ru_data
                ru_id = str(ru.id)
                opening_key = f'opening_{ru_id}'
                action_key = f'action_{ru_id}'
                
                if opening_key not in request.POST or request.POST[opening_key] == "" or action_key not in request.POST:
                    continue

                try:
                    input_value = int(request.POST[opening_key])
                    action = request.POST[action_key]
                    
                    # Get last closing reading
                    last_daily = RechargeUnitDailyReading.objects.filter(
                        recharge_unit=ru
                    ).order_by('-date').first()
                    last_closing = last_daily.closing_reading if last_daily else 0
                    
                    # Calculate opening reading
                    opening_reading = (last_closing + input_value) if action == 'add' else input_value
                    
                    # Update or create monthly opening
                    RechargeUnitMonthlyOpening.objects.update_or_create(
                        recharge_unit=ru,
                        date=reset_history.date,
                        defaults={
                            'opening_reading': opening_reading,
                            'reset_history': reset_history
                        }
                    )
                    
                    processed_count += 1
                    
                except (ValueError, TypeError) as e:
                    messages.error(request, f"Invalid input for {ru.name}: {e}")
                    continue

            if processed_count > 0:
                messages.success(request, f"Successfully processed {processed_count} recharge units!")
            else:
                reset_history.delete()
                messages.warning(request, "No recharge units were processed")
                #reset_history.delete()  # Clean up unused history

        return redirect('grand_reset')
    

@login_required
def reset_single_subunit(request, subunit_id):
    if request.method == 'POST':
        subunit = get_object_or_404(Subunit, pk=subunit_id)
        today = timezone.now().date()
        
        # Check for existing reset today
        if subunit.monthlyopeningsub_set.filter(date=today).exists():
            messages.warning(request, f'{subunit.name} already reset today!')
            #return redirect('unit_subunits', unit_id=subunit.unit.id)
            return JsonResponse({'status': 'error', 'message': f'{subunit.name} already reset today!'})
        
        with transaction.atomic():
            try:
                reset_history = ResetHistory.objects.create(
                    action_type='subunit_reset',
                    date=today
                )
                MonthlyOpeningSub.objects.create(
                    subunit=subunit,
                    date=today,
                    amount_opening=0,
                    dispenser_opening=0,
                    reset_history=reset_history
                )
                
                messages.success(request, f'{subunit.name} reset successfully!')
                return JsonResponse({'status': 'success', 'message': f'{subunit.name} reset successfully!'})
        
            except Exception as e:
                if reset_history:
                    reset_history.delete()
                messages.error(request, f'Error resetting {subunit.name}: {str(e)}')
                return JsonResponse({'status': 'error', 'message': f'Error resetting {subunit.name}: {str(e)}'})
                #return redirect('unit_subunits', unit_id=subunit.unit.id)
        

        #return redirect('unit_subunits', unit_id=subunit.unit.id)
    return redirect('grand_reset')


@login_required
def reset_unit_subunits(request, unit_id):
    if request.method == 'POST':
        unit = get_object_or_404(Unit, pk=unit_id)
        today = timezone.now().date()
        subunits = unit.subunit_set.filter(is_deleted=False)
        
        with transaction.atomic():
            reset_history = ResetHistory.objects.create(
                action_type='subunit_reset',
                date=today
            )
            
            created_count = 0
            for subunit in subunits:
                # Skip if already has reset today
                if not subunit.monthlyopeningsub_set.filter(date=today).exists():
                    MonthlyOpeningSub.objects.create(
                        subunit=subunit,
                        date=today,
                        amount_opening=0,
                        dispenser_opening=0,
                        reset_history=reset_history
                    )
                    created_count += 1
            
            if created_count == 0:
                messages.warning(request, 'All subunits already reset today!')
                reset_history.delete()
                return JsonResponse({'status': 'error', 'message': f'All subunits already reset today!'})
                #reset_history.delete()
            else:
                messages.success(request, f'Reset {created_count} subunits!')

        return JsonResponse({'status': 'success', 'message': f'Reset {created_count} subunits!'})
        #return redirect('unit_subunits', unit_id=unit_id)
    return redirect('grand_reset')






####################################################################################report


@login_required
def admin_monthly_reports(request):
    # Get all reset intervals across all units
    all_intervals = []
    units = Unit.objects.filter(is_deleted=False)
    selected_month = request.GET.get('month')
    selected_unit = request.GET.get('unit')

    for unit in units:
        intervals = get_reset_intervals(unit)
        for interval in intervals:
            totals = calculate_interval_totals(unit, interval['start'], interval['end'])
            interval.update(totals)
            interval['unit'] = unit
            all_intervals.append(interval)

     # Apply filters
    if selected_month:
        try:
            filter_date = datetime.strptime(selected_month, "%Y-%m").date()
            start_month = filter_date.replace(day=1)
            end_month = (start_month + relativedelta(months=1)) - relativedelta(days=1)
            
            # Filter intervals overlapping with month
            all_intervals = [
                i for i in all_intervals
                if not (i['end'] < start_month or i['start'] > end_month)
            ]
        except ValueError:
            messages.error(request, "Invalid month format")
            return redirect('admin_monthly_reports')

    if selected_unit:
        all_intervals = [i for i in all_intervals if i['unit'].id == int(selected_unit)]

    # Sort all intervals by end date
    all_intervals = sorted(all_intervals, key=lambda x: x['end'], reverse=True)
    
    # Pagination
    paginator = Paginator(all_intervals, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin_dashboard/monthly_reports.html', {
        'page_obj': page_obj,
        'units': units,
        'selected_month': selected_month,
        'selected_unit': selected_unit
    })





# views.py
@login_required
def generate_monthly_report(request, start_date=None, end_date=None):
    # Get unit from request (admin can specify any unit)
    unit_id = request.GET.get('unit')
    unit = get_object_or_404(Unit, id=unit_id) if unit_id else None
    
    # Permission check
    # if not request.user.is_admin:
    #     if not unit or unit != request.user.unit:
    #         #raise PermissionDenied("You don't have permission to view this report")
    #         pass
    #     unit = request.user.unit

    # # Date validation
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            messages.error(request, "Invalid date format")
            return redirect('admin_monthly_reports')
        
    #     # Verify date range is valid
    #     valid_intervals = get_reset_intervals(unit)
    #     valid = any(
    #         interval['start'] <= start_date and interval['end'] >= end_date
    #         for interval in valid_intervals
    #     )
        
    #     if not valid:
    #         messages.error(request, "Invalid date range selected")
    #         return redirect('admin_monthly_reports')

    # Data aggregation using existing logic
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

    expenses = Expense.objects.filter(
        unit=unit,
        date__range=[start_date, end_date]
    )
    expense_categories = {}
    for expense in expenses:
        category = expense.get_category_display()
        expense_categories[category] = expense_categories.get(category, 0) + expense.amount

    workers = Worker.objects.filter(unit=unit)
    attendance_data = []
    for worker in workers:
        present_days = Attendance.objects.filter(
            worker=worker,
            date__range=[start_date, end_date],
            is_present=True
        ).count()
        attendance_data.append({'worker': worker, 'present_days': present_days})

    total_income = total_subunit_income + total_recharge_income
    total_expense = sum(expense_categories.values(), 0)
    cash_in_hand = total_income - total_expense

    context = {
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
    return render(request, 'admin_dashboard/admin_monthly_report.html', context)