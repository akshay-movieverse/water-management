
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import RechargeUnit, Unit, Subunit, CustomUser


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from django.shortcuts import render, redirect, get_object_or_404
from .models import Unit, Subunit, CustomUser
from .forms import UnitForm, SubunitForm, ManagerForm
from django.contrib.auth.decorators import login_required

@login_required
def admin_dashboard(request):
    return render(request, 'admin_dashboard/dashboard.html')

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



############################################################################################
@login_required
def manager_list(request):
    managers = CustomUser.objects.filter(is_manager=True)
    return render(request, 'admin_dashboard/manager_list.html', {'managers': managers})


from django.db import IntegrityError
from django.core.exceptions import ValidationError
@login_required
def add_manager(request):
    units = Unit.objects.filter(is_deleted=False)

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
from manager_dashboard.models import Expense, DailyReading, Attendance
from admin_dashboard.models import ReportGeneration

from django.shortcuts import render
from datetime import date
from .models import ReportGeneration, Unit

def report_list(request):
    today = date.today()

    # Get filters from request
    selected_date = request.GET.get('date')
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
    print(available_dates)

    return render(request, 'admin_dashboard/report_list.html', {
        'reports': reports,
        'units': units,
        'today': today,
        'available_dates': available_dates  # Pass dates to template
    })


def report_detail(request, report_id):
    report = get_object_or_404(ReportGeneration, id=report_id)
    
    subunit_readings = DailyReading.objects.filter(date=report.date, subunit__unit=report.unit)
    expenses = Expense.objects.filter(date=report.date, unit=report.unit)
    attendance = Attendance.objects.filter(date=report.date, worker__unit=report.unit)

    total_income = sum(r.amount_rs() for r in subunit_readings)
    total_expense = sum(e.amount for e in expenses)
    total_water_supply = sum(r.water_supply() for r in subunit_readings)
    cash_in_hand = total_income - total_expense

    return render(request, 'admin_dashboard/admin_report.html', {
        'date': report.date,
        'report': report,
        'subunit_readings': subunit_readings,
        'expenses': expenses,
        'attendance': attendance,
        'total_income': total_income,
        'total_expense': total_expense,
        'total_water_supply': total_water_supply,
        'cash_in_hand': cash_in_hand,
    })
