from django.urls import path
from . import views

urlpatterns = [
    path('', views.employee_home, name='employee_home'),
    path('my_dashboard/card_usage/', views.card_usage, name='card_usage'),
    path('my_dashboard/my_ec_card/', views.my_ec_card, name='my_ec_card'),
    path('my_dashboard/apply_ec_card/', views.apply_ec_card, name='apply_ec_card'),
    path('support/faq/', views.faq, name='faq'),
    path('support/report_issues/', views.report_issues, name='report_issues'),
    path('access-denied/', views.access_denied, name='access_denied'),  # Add this line
]