
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

        # Ensure unique username
        if CustomUser.objects.filter(username=username).exists():
            return render(request, 'admin_dashboard/add_manager.html', {
                'units': units,
                'error': 'Username already exists. Choose another one.'
            })

        manager = CustomUser.objects.create(
            username=username,
            first_name=name,
            is_manager=True,
            unit=unit,
            email=email or '',
            phone_number=phone or '',
            password=make_password(password)
        )

        return redirect('manager_list')

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
