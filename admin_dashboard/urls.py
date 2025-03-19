from django.urls import path
from .views import (
    add_subunit_recharge, admin_dashboard, add_unit,  delete_recharge_unit, edit_unit, unit_list, unit_detail, delete_unit,
    delete_subunit, add_manager, manager_list, delete_manager
)

urlpatterns = [
    path('', admin_dashboard, name='admin_dashboard'),

    path('units/', unit_list, name='unit_list'),
    path('units/add/', add_unit, name='add_unit'),
    path('units/<int:unit_id>/edit/', edit_unit, name='edit_unit'),
    path('units/<int:unit_id>/', unit_detail, name='unit_detail'),
    path('units/<int:unit_id>/subunits-recharges/add/', add_subunit_recharge, name='add_subunit_recharge'),
    path('units/<int:unit_id>/delete/', delete_unit, name='delete_unit'),  # ✅ Added Delete Unit URL
    path('subunit/<int:subunit_id>/delete/', delete_subunit, name='delete_subunit'),
    path('recharge/<int:recharge_unit_id>/delete/', delete_recharge_unit, name='delete_recharge_unit'),

]

from .views import (
    manager_list, add_manager, edit_manager, delete_manager
)

urlpatterns += [  # Adding manager routes
    path('managers/', manager_list, name='manager_list'),
    path('managers/add/', add_manager, name='add_manager'),
    path('managers/<int:manager_id>/edit/', edit_manager, name='edit_manager'),
    path('managers/<int:manager_id>/delete/', delete_manager, name='delete_manager'),
]