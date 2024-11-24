from django.urls import path
from . import views


urlpatterns = [
    path('', views.admin_home, name='admin_home'),  # Home route for the admin panel
    path('cardholders/view_all_users/', views.view_all_users, name='view_all_users'),
    path('cardholders/<int:cardholder_id>/', views.manage_user_details, name='manage_user_details'),
    path('cardholders/', views.manage_card_holders, name="manage_card_holders"),
    path('cardholders/delete/<int:cardholder_id>/', views.delete_cardholder, name="delete_cardholder"),
    path('cardholders/search/', views.search_cardholders, name='search_cardholders'), # Search

    path('ec_card/issue_card/', views.issue_card, name='issue_card'),
    path('ec_card/revoke_card/<int:cardholder_id>/', views.revoke_card, name='revoke_card'),
    path('ec_card/edit_card/<int:cardholder_id>/', views.edit_card, name='edit_card'),
    path('ec_card/reissue_card/<int:cardholder_id>/', views.reissue_card, name='reissue_card'),
    path('ec_card/upload_card_faceplate/', views.upload_card_faceplate, name='upload_card_faceplate'),
    path('ec_card/view_card_faceplate/', views.view_card_faceplate, name='view_card_faceplate'),
    
    path('reports/all_pos_transactions/', views.reports_dashboard, name='reports_dashboard'),
    path('reports/total_discounts_per_store/', views.total_discounts_per_store, name='total_discounts_per_store'),
    path('reports/total_discounts_per_employee/', views.total_discounts_per_employee, name='total_discounts_per_employee'),
    path('reports/drilldown_store/<str:store_name>/', views.drilldown_store, name='drilldown_store'),
    path('reports/drilldown_employee/', views.drilldown_employee, name='drilldown_employee'),
    
    path('reports/view_sent_email_reports/', views.view_sent_email_reports, name='view_sent_email_reports'),
    
    path('support/manage_user_guides/', views.manage_user_guides, name='manage_user_guides'),
    path('support/manage_report_issues/', views.manage_report_issues, name='manage_report_issues'),
]
