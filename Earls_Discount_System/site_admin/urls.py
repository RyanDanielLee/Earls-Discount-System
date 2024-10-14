from django.urls import path
from . import views

app_name = 'site_admin'

urlpatterns = [
    path('', views.admin_home, name='admin_home'),  # Home route for the admin panel
    path('cardholders/view_all_users/', views.view_all_users, name='view_all_users'),
    path('cardholders/manage_user_details/', views.manage_user_details, name='manage_user_details'),
    
    path('ec_card/issue_card/', views.issue_card, name='issue_card'),
    path('ec_card/revoke_card/', views.revoke_card, name='revoke_card'),
    path('ec_card/upload_card_faceplates/', views.upload_card_faceplates, name='upload_card_faceplates'),
    
    path('reports/all_pos_transactions/', views.all_pos_transactions, name='all_pos_transactions'),
    path('reports/total_discounts_per_store/', views.total_discounts_per_store, name='total_discounts_per_store'),
    path('reports/total_discounts_per_employee/', views.total_discounts_per_employee, name='total_discounts_per_employee'),
    path('reports/view_sent_email_reports/', views.view_sent_email_reports, name='view_sent_email_reports'),
    
    path('support/manage_user_guides/', views.manage_user_guides, name='manage_user_guides'),
    path('support/manage_report_issues/', views.manage_report_issues, name='manage_report_issues'),
]
