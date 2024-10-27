from django.shortcuts import render
from django.http import HttpResponse

# Home route for admin
def admin_home(request):
    return render(request, 'admin/home.html')

# Cardholders
def view_all_users(request):
    return HttpResponse("View All Users Page")

def manage_user_details(request):
    return HttpResponse("Manage User Details Page")

def manage_card_holders(request):
    return render(request, 'cardholder/cardholder.html')

# EC Card
def issue_card(request):
    return render(request, 'eccard/issue-card.html')

def revoke_card(request):
    return HttpResponse("Revoke Card Page")

def upload_card_faceplates(request):
    return render(request, 'eccard/upload-faceplates.html')

# Reports
def reports_dashboard(request):
    return render(request, 'reports/reports-dashboard.html')

def total_discounts_per_store(request):
    return render(request, 'reports/reports-store.html')

def drilldown_store(request):
    return render(request, 'reports/drildown-store.html')

def total_discounts_per_employee(request):
    return render(request, 'reports/reports-employee.html')

def drilldown_employee(request):
    return render(request, 'reports/drilldown-employee.html')

def view_sent_email_reports(request):
    return HttpResponse("View Sent Email Reports Page")

# Supports
def manage_user_guides(request):
    return HttpResponse("Manage User Guides Page")

def manage_report_issues(request):
    return HttpResponse("Manage Report Issues Page")
