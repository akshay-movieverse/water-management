from django.urls import path
from .views import (
    FillRechargeView, GrandResetView, UnitRechargeUnitsView, UnitSubunitsView, add_subunit_recharge, admin_dashboard, add_unit, admin_monthly_reports,  delete_recharge_unit, delete_reset, edit_unit, generate_monthly_report, history_view, report_detail, report_list, reset_single_subunit, reset_unit_subunits, subunit_reset, unit_list, unit_detail, delete_unit,
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

    path('reports/', report_list, name='admin_reports'),
    path('reports/<int:report_id>/', report_detail, name='admin_report_detail'),

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

urlpatterns += [  # Adding manager routes
path('grand-reset/', GrandResetView.as_view(), name='grand_reset'),
path('subunit-reset/', subunit_reset, name='subunit_reset'),
path('fill-recharge/', FillRechargeView.as_view(), name='fill_recharge'),


# urls.py
path('grand-reset/unit/<int:unit_id>/subunits/', UnitSubunitsView.as_view(), name='unit_subunits'),
path('grand-reset/unit/<int:unit_id>/recharge-units/', UnitRechargeUnitsView.as_view(), name='unit_recharge_units'),
path('reset-subunit/<int:subunit_id>/', reset_single_subunit, name='reset_single_subunit'),

path('reset-unit-subunits/<int:unit_id>/', reset_unit_subunits, name='reset_unit_subunits'),


path('history/', history_view, name='history'),
path('delete-reset/<int:reset_id>/', delete_reset, name='delete_reset'),



path('admin-monthly-reports/', admin_monthly_reports, name='admin_monthly_reports'),

path('generate-monthly-report/<str:start_date>/<str:end_date>/', generate_monthly_report, name='admin_generate_monthly_report'),

]
